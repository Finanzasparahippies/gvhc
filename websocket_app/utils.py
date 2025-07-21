# C:\Users\Agent\Documents\Zoom\config\files\gvhc\websocket_app\websocket_utils.py

from fastapi import WebSocket # You'll still need this import here for type hinting

# We need a way to manage connections that's accessible from both server.py and here
# A simple list will work, but for more robust solutions, consider a manager class.
# For now, let's keep it simple and assume 'active_connections' is passed or managed globally.

active_connections: list[WebSocket] = [] # Define it here

async def broadcast_new_data(data: dict):
    # Ensure we're only iterating over a copy to avoid issues if connections change during iteration
    connections_to_remove = []
    for connection in list(active_connections): # Iterate over a copy
        try:
            await connection.send_json(data)
        except Exception as e:
            print(f"Error broadcasting to connection: {e}")
            # If sending fails, assume connection is dead and mark for removal
            connections_to_remove.append(connection)
    
    # Remove dead connections
    for conn in connections_to_remove:
        if conn in active_connections: # Check if it's still there
            active_connections.remove(conn)