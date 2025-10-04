#!/usr/bin/env python3

"""Generate a visual flow graph for the dental clinic assistant conversation flow."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
from typing import Dict, List, Tuple

def create_flow_graph():
    """Create and display the conversation flow graph."""
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Define nodes with their types and descriptions
    nodes = {
        # Entry point
        "initial": {"type": "entry", "label": "Welcome\n& Main Menu", "color": "#4CAF50"},
        
        # Information nodes
        "clinic_info": {"type": "info", "label": "Clinic Info\n(Address, Hours)", "color": "#2196F3"},
        "services_info": {"type": "info", "label": "Services Info\n(Treatments, Prices)", "color": "#2196F3"},
        "dentist_info": {"type": "info", "label": "Dentist Info\n(Doctors, Specialties)", "color": "#2196F3"},
        "insurance_info": {"type": "info", "label": "Insurance Info\n(Accepted Plans)", "color": "#2196F3"},
        
        # Appointment booking flow
        "schedule_appointment": {"type": "booking", "label": "Start Booking\nAppointment", "color": "#FF9800"},
        "patient_info": {"type": "booking", "label": "Collect Patient\nName & Phone", "color": "#FF9800"},
        "service_selection": {"type": "booking", "label": "Select\nService Type", "color": "#FF9800"},
        "date_time_selection": {"type": "booking", "label": "Select Date\n& Time", "color": "#FF9800"},
        "alternative_times": {"type": "booking", "label": "Show Alternative\nTime Slots", "color": "#FFC107"},
        "appointment_confirmation": {"type": "booking", "label": "Confirm\nAppointment Details", "color": "#FF9800"},
        "appointment_success": {"type": "success", "label": "Booking Success\n& Confirmation", "color": "#4CAF50"},
        
        # Existing appointment management
        "manage_appointment": {"type": "management", "label": "Manage Existing\nAppointment", "color": "#9C27B0"},
        "find_appointment": {"type": "management", "label": "Find Appointment\nby Name/Phone", "color": "#9C27B0"},
        "appointment_options": {"type": "management", "label": "Cancel or\nReschedule Options", "color": "#9C27B0"},
        "appointment_not_found": {"type": "error", "label": "Appointment\nNot Found", "color": "#F44336"},
        
        # Cancellation flow
        "cancel_appointment": {"type": "management", "label": "Cancel\nAppointment", "color": "#9C27B0"},
        "cancellation_success": {"type": "success", "label": "Cancellation\nSuccess", "color": "#4CAF50"},
        "cancellation_error": {"type": "error", "label": "Cancellation\nError", "color": "#F44336"},
        
        # Rescheduling flow
        "reschedule_appointment": {"type": "management", "label": "Reschedule\nAppointment", "color": "#9C27B0"},
        "reschedule_times": {"type": "management", "label": "New Time\nSelection", "color": "#9C27B0"},
        "reschedule_success": {"type": "success", "label": "Reschedule\nSuccess", "color": "#4CAF50"},
        
        # Exit
        "end_conversation": {"type": "exit", "label": "End\nConversation", "color": "#607D8B"}
    }
    
    # Add nodes to graph
    for node_id, node_data in nodes.items():
        G.add_node(node_id, **node_data)
    
    # Define edges (conversation flow connections)
    edges = [
        # From initial node
        ("initial", "clinic_info"),
        ("initial", "services_info"),
        ("initial", "dentist_info"),
        ("initial", "insurance_info"),
        ("initial", "schedule_appointment"),
        ("initial", "manage_appointment"),
        
        # Information nodes back to main
        ("clinic_info", "initial"),
        ("services_info", "initial"),
        ("dentist_info", "initial"),
        ("insurance_info", "initial"),
        
        # Information nodes to booking
        ("clinic_info", "schedule_appointment"),
        ("services_info", "schedule_appointment"),
        ("dentist_info", "schedule_appointment"),
        ("insurance_info", "schedule_appointment"),
        
        # Appointment booking flow
        ("schedule_appointment", "patient_info"),
        ("patient_info", "service_selection"),
        ("service_selection", "date_time_selection"),
        ("date_time_selection", "appointment_confirmation"),
        ("date_time_selection", "alternative_times"),
        ("alternative_times", "appointment_confirmation"),
        ("alternative_times", "date_time_selection"),
        ("appointment_confirmation", "appointment_success"),
        ("appointment_confirmation", "service_selection"),  # modify details
        ("appointment_success", "initial"),
        ("appointment_success", "end_conversation"),
        
        # Existing appointment management
        ("manage_appointment", "find_appointment"),
        ("find_appointment", "appointment_options"),
        ("find_appointment", "appointment_not_found"),
        ("appointment_not_found", "find_appointment"),
        ("appointment_not_found", "schedule_appointment"),
        
        # Cancellation flow
        ("appointment_options", "cancel_appointment"),
        ("cancel_appointment", "cancellation_success"),
        ("cancel_appointment", "cancellation_error"),
        ("cancellation_success", "initial"),
        ("cancellation_error", "initial"),
        
        # Rescheduling flow
        ("appointment_options", "reschedule_appointment"),
        ("reschedule_appointment", "reschedule_times"),
        ("reschedule_times", "reschedule_success"),
        ("reschedule_times", "reschedule_appointment"),
        ("reschedule_success", "initial"),
        
        # Back to main from various points
        ("patient_info", "initial"),
        ("service_selection", "initial"),
        ("date_time_selection", "initial"),
        ("alternative_times", "initial"),
        ("appointment_confirmation", "initial"),
        ("manage_appointment", "initial"),
        ("appointment_options", "initial"),
        ("reschedule_appointment", "initial"),
    ]
    
    # Add edges to graph
    G.add_edges_from(edges)
    
    # Create the plot
    plt.figure(figsize=(20, 16))
    
    # Use a hierarchical layout
    pos = create_hierarchical_layout(G, nodes)
    
    # Draw nodes with different shapes and colors based on type
    for node_id, (x, y) in pos.items():
        node_data = nodes[node_id]
        color = node_data["color"]
        label = node_data["label"]
        node_type = node_data["type"]
        
        # Different shapes for different node types
        if node_type == "entry":
            shape = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=color, edgecolor="black", linewidth=2)
        elif node_type == "success":
            shape = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=color, edgecolor="darkgreen", linewidth=2)
        elif node_type == "error":
            shape = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                                 boxstyle="round,pad=0.1", 
                                 facecolor=color, edgecolor="darkred", linewidth=2)
        else:
            shape = FancyBboxPatch((x-0.8, y-0.3), 1.6, 0.6, 
                                 boxstyle="round,pad=0.05", 
                                 facecolor=color, edgecolor="gray", linewidth=1)
        
        plt.gca().add_patch(shape)
        plt.text(x, y, label, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Draw edges with different styles
    for edge in G.edges():
        start_pos = pos[edge[0]]
        end_pos = pos[edge[1]]
        
        # Different arrow styles for different types of connections
        if edge[1] == "initial":  # Back to main
            style = dict(arrowstyle='->', color='gray', alpha=0.6, linestyle='--')
        elif "success" in edge[1] or "error" in edge[1]:  # To terminal states
            style = dict(arrowstyle='->', color='darkgreen', alpha=0.8, linewidth=2)
        else:  # Regular flow
            style = dict(arrowstyle='->', color='black', alpha=0.7)
        
        plt.annotate('', xy=end_pos, xytext=start_pos,
                    arrowprops=style)
    
    # Create legend
    legend_elements = [
        mpatches.Rectangle((0, 0), 1, 1, facecolor="#4CAF50", label="Entry/Success Points"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor="#2196F3", label="Information Nodes"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor="#FF9800", label="Appointment Booking"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor="#9C27B0", label="Appointment Management"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor="#F44336", label="Error States"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor="#607D8B", label="Exit Point"),
    ]
    
    plt.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1, 1))
    
    # Set title and clean up the plot
    plt.title("🦷 Dental Clinic Assistant - Conversation Flow Graph\n" + 
             "Refactored OOP Architecture", fontsize=16, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()
    
    # Save the graph
    plt.savefig('dental_clinic_flow_graph.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return G

def create_hierarchical_layout(G, nodes):
    """Create a custom hierarchical layout for the flow graph."""
    pos = {}
    
    # Define levels and their nodes
    levels = {
        0: ["initial"],  # Entry point
        1: ["clinic_info", "services_info", "dentist_info", "insurance_info", 
            "schedule_appointment", "manage_appointment"],  # Main options
        2: ["patient_info", "find_appointment"],  # Next level inputs
        3: ["service_selection", "appointment_options", "appointment_not_found"],  # Choices
        4: ["date_time_selection", "cancel_appointment", "reschedule_appointment"],  # Actions
        5: ["alternative_times", "appointment_confirmation", "reschedule_times", 
            "cancellation_success", "cancellation_error"],  # Confirmations
        6: ["appointment_success", "reschedule_success"],  # Success states
        7: ["end_conversation"]  # Exit
    }
    
    # Position nodes in levels
    for level, node_list in levels.items():
        y = -level * 2  # Vertical spacing
        node_count = len(node_list)
        
        for i, node in enumerate(node_list):
            if node_count == 1:
                x = 0
            else:
                # Distribute nodes horizontally
                x = (i - (node_count - 1) / 2) * 4
            
            pos[node] = (x, y)
    
    return pos

def print_flow_statistics(G):
    """Print some statistics about the flow graph."""
    print("\n🔢 Flow Graph Statistics:")
    print(f"📊 Total Nodes: {G.number_of_nodes()}")
    print(f"🔗 Total Connections: {G.number_of_edges()}")
    print(f"🎯 Entry Points: 1 (initial)")
    print(f"🏁 Exit Points: 1 (end_conversation)")
    
    # Count nodes by type
    node_types = {}
    for node in G.nodes(data=True):
        node_type = node[1].get('type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    print("\n📋 Node Types:")
    for node_type, count in node_types.items():
        print(f"   {node_type.title()}: {count}")

if __name__ == "__main__":
    print("🦷 Generating Dental Clinic Conversation Flow Graph...")
    
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
        
        G = create_flow_graph()
        print_flow_statistics(G)
        print("\n✅ Flow graph generated successfully!")
        print("📁 Saved as: dental_clinic_flow_graph.png")
        
    except ImportError as e:
        print(f"❌ Missing required libraries: {e}")
        print("📦 Install with: pip install matplotlib networkx")