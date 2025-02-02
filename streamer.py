import asyncio
import websockets
import json
import argparse

import socket

connected_writers = []  # We'll track Raylib clients here

async def handle_local_client(reader, writer):
    """Handle a single Raylib TCP client."""
    global connected_writers
    connected_writers.append(writer)
    client_addr = writer.get_extra_info("peername")
    print(f"[TCP] Raylib client connected: {client_addr}")

    try:
        while True:
            data = await reader.read(100)
            if not data:
                break  # client disconnected
            print(f"[TCP] Received from Raylib client: {data.decode().strip()}")
    except asyncio.CancelledError:
        pass
    finally:
        print(f"[TCP] Raylib client disconnected: {client_addr}")
        connected_writers.remove(writer)
        writer.close()
        await writer.wait_closed()

async def forward_events_from_bluesky(ws_uri, filter_text, filter_lang):
    print("[WS] Connecting to JetStream endpoint...")
    async with websockets.connect(ws_uri) as ws:
        print("[WS] Connected to JetStream!")

        lang_filters = []
        if filter_lang:
            lang_filters = [lang.strip().lower() for lang in filter_lang.split(",") if lang.strip()]

        async for message in ws:
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue

            commit_data = data.get("commit", {})
            record = commit_data.get("record", {})

            text = record.get("text", "")
            text_lower = text.lower()

            if filter_text and filter_text not in text_lower:
                continue

            post_langs = record.get("langs", [])  # e.g. ["en","de"]
            post_langs_lower = [l.lower() for l in post_langs if isinstance(l, str)]

            if lang_filters:
                if not any(lang in lang_filters for lang in post_langs_lower):
                    continue

            cid = commit_data.get("cid", "???")
            print(f"[MATCH] CID={cid}, text={text[:50]}, langs={post_langs}")

            text_escaped = text.replace("\n", "\\n").replace("\r", "")
            msg = f"NEW|{text_escaped}\n"
            msg_bytes = msg.encode("utf-8", errors="ignore")

            disconnected = []
            for w in connected_writers:
                try:
                    w.write(msg_bytes)
                    await w.drain()
                except (ConnectionError, OSError):
                    disconnected.append(w)

            # Clean up any disconnected clients
            for dw in disconnected:
                connected_writers.remove(dw)

async def main(args):
    # Start a local TCP server for Raylib
    server = await asyncio.start_server(handle_local_client, args.local_host, args.local_port)
    addr = server.sockets[0].getsockname()
    print(f"[TCP] Listening for Raylib game at {addr}")

    # Start reading from the Bluesky WebSocket
    ws_task = asyncio.create_task(forward_events_from_bluesky(
        args.ws_uri, 
        args.filter_text,
        args.filter_lang
    ))

    # Keep serving local clients until stopped
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bluesky JetStream client with local TCP server to Raylib."
    )
    parser.add_argument(
        "--ws-uri",
        type=str,
        default="wss://jetstream2.us-east.bsky.network/subscribe?wantedCollections=app.bsky.feed.post",
        help="JetStream WebSocket URI"
    )
    parser.add_argument(
        "--local-host",
        type=str,
        default="127.0.0.1",
        help="Local interface for Raylib game to connect"
    )
    parser.add_argument(
        "--local-port",
        type=int,
        default=12345,
        help="Local TCP port for Raylib game"
    )
    parser.add_argument(
        "--filter-text",
        dest="filter_text",
        type=str,
        default="",
        help="Keyword to filter text in app.bsky.feed.post events."
    )
    parser.add_argument(
        "--filter-lang",
        dest="filter_lang",
        type=str,
        default="",
        help="Comma-separated languages to match. If set, post must contain ANY of these langs."
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("Shutting down...")
