import osmnx as ox
import matplotlib.pyplot as plt

def download_chennai_network():
    print("🌍 Contacting OpenStreetMap... this might take 30-60 seconds...")
    
    # 1. Define the place
    # We use a broad query to get the Greater Chennai Corporation area
    place_name = "Chennai, India"
    
    # 2. Download the graph
    # network_type='drive' means we only want roads for cars (no walking paths)
    # simplify=True cleans up the messy nodes automatically
    G = ox.graph_from_place(place_name, network_type='drive', simplify=True)
    
    print(f"✅ Download complete!")
    print(f"   Nodes (Intersections): {len(G.nodes)}")
    print(f"   Edges (Road Segments): {len(G.edges)}")
    
    # 3. Visual check
    print("🎨 Generating map plot... (A window will pop up)")
    ox.plot_graph(G, node_size=0, edge_linewidth=0.5, show=True)

if __name__ == "__main__":
    download_chennai_network()