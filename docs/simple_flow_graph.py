#!/usr/bin/env python3

"""Generate a simple visual flow graph for the dental clinic assistant."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as patches

def create_simple_flow_graph():
    """Create a simplified flow graph."""
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    
    # Define colors for different node types
    colors = {
        'entry': '#4CAF50',      # Green
        'info': '#2196F3',       # Blue  
        'booking': '#FF9800',    # Orange
        'management': '#9C27B0', # Purple
        'success': '#4CAF50',    # Green
        'error': '#F44336',      # Red
        'exit': '#607D8B'        # Blue Grey
    }
    
    # Define node positions and properties
    nodes = [
        # Level 0 - Entry
        {'name': 'INITIAL\n(Welcome)', 'pos': (8, 10), 'type': 'entry', 'size': (2, 1)},
        
        # Level 1 - Main Options
        {'name': 'Clinic\nInfo', 'pos': (2, 8), 'type': 'info', 'size': (1.5, 0.8)},
        {'name': 'Services\nInfo', 'pos': (4.5, 8), 'type': 'info', 'size': (1.5, 0.8)},
        {'name': 'Dentist\nInfo', 'pos': (7, 8), 'type': 'info', 'size': (1.5, 0.8)},
        {'name': 'Insurance\nInfo', 'pos': (9.5, 8), 'type': 'info', 'size': (1.5, 0.8)},
        {'name': 'Schedule\nAppointment', 'pos': (12, 8), 'type': 'booking', 'size': (1.5, 0.8)},
        {'name': 'Manage\nAppointment', 'pos': (14.5, 8), 'type': 'management', 'size': (1.5, 0.8)},
        
        # Level 2 - Booking Flow
        {'name': 'Patient\nInfo', 'pos': (10, 6), 'type': 'booking', 'size': (1.5, 0.8)},
        {'name': 'Find\nAppointment', 'pos': (14.5, 6), 'type': 'management', 'size': (1.5, 0.8)},
        
        # Level 3 - Detailed Steps
        {'name': 'Service\nSelection', 'pos': (10, 4), 'type': 'booking', 'size': (1.5, 0.8)},
        {'name': 'Appointment\nOptions', 'pos': (14.5, 4), 'type': 'management', 'size': (1.5, 0.8)},
        {'name': 'Not Found', 'pos': (17, 4), 'type': 'error', 'size': (1.5, 0.8)},
        
        # Level 4 - Time Selection
        {'name': 'Date & Time\nSelection', 'pos': (8, 2), 'type': 'booking', 'size': (1.5, 0.8)},
        {'name': 'Alternative\nTimes', 'pos': (10.5, 2), 'type': 'booking', 'size': (1.5, 0.8)},
        {'name': 'Cancel\nAppointment', 'pos': (13, 2), 'type': 'management', 'size': (1.5, 0.8)},
        {'name': 'Reschedule\nAppointment', 'pos': (15.5, 2), 'type': 'management', 'size': (1.5, 0.8)},
        
        # Level 5 - Confirmation
        {'name': 'Confirm\nAppointment', 'pos': (9, 0), 'type': 'booking', 'size': (1.5, 0.8)},
        {'name': 'Success\nStates', 'pos': (12, 0), 'type': 'success', 'size': (1.5, 0.8)},
        {'name': 'Error\nStates', 'pos': (15, 0), 'type': 'error', 'size': (1.5, 0.8)},
        
        # Level 6 - Exit
        {'name': 'END\nConversation', 'pos': (8, -2), 'type': 'exit', 'size': (2, 1)},
    ]
    
    # Draw nodes
    for node in nodes:
        x, y = node['pos']
        w, h = node['size']
        color = colors[node['type']]
        
        # Create rounded rectangle
        box = FancyBboxPatch(
            (x - w/2, y - h/2), w, h,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor='black',
            linewidth=1,
            alpha=0.8
        )
        ax.add_patch(box)
        
        # Add text
        ax.text(x, y, node['name'], ha='center', va='center', 
                fontsize=9, fontweight='bold', wrap=True)
    
    # Draw main flow arrows
    arrows = [
        # From initial to main options
        ((8, 9.5), (2.75, 8.4)),    # To clinic info
        ((8, 9.5), (5.25, 8.4)),    # To services info  
        ((8, 9.5), (7.75, 8.4)),    # To dentist info
        ((8, 9.5), (10.25, 8.4)),   # To insurance info
        ((8, 9.5), (12.75, 8.4)),   # To schedule
        ((8, 9.5), (15.25, 8.4)),   # To manage
        
        # Booking flow
        ((12, 7.6), (10.75, 6.4)),  # Schedule to patient info
        ((10, 5.6), (10, 4.4)),     # Patient info to service selection
        ((10, 3.6), (8.75, 2.4)),   # Service selection to date/time
        ((8, 1.6), (9, 0.4)),       # Date/time to confirm
        ((9, -0.4), (8, -1.5)),     # Confirm to end
        
        # Management flow
        ((14.5, 7.6), (14.5, 6.4)), # Manage to find
        ((14.5, 5.6), (14.5, 4.4)), # Find to options
        ((14.5, 3.6), (13.75, 2.4)), # Options to cancel
        ((14.5, 3.6), (15.25, 2.4)), # Options to reschedule
        
        # Alternative flow
        ((8.5, 2.4), (10, 2.4)),    # Date/time to alternatives
        ((10.5, 1.6), (9.25, 0.4)), # Alternatives to confirm
        
        # Success flows
        ((13, 1.6), (12.25, 0.4)),  # Cancel to success
        ((15.5, 1.6), (12.75, 0.4)), # Reschedule to success
        ((12, -0.4), (8.5, -1.5)),  # Success to end
    ]
    
    # Draw arrows
    for start, end in arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color='black', alpha=0.6, lw=1))
    
    # Add back-to-main arrows (dashed)
    back_arrows = [
        ((2.75, 7.6), (7.5, 9.5)),   # Info nodes back to main
        ((5.25, 7.6), (7.75, 9.5)),
        ((7.75, 7.6), (8, 9.5)),
        ((10.25, 7.6), (8.25, 9.5)),
    ]
    
    for start, end in back_arrows:
        ax.annotate('', xy=end, xytext=start,
                   arrowprops=dict(arrowstyle='->', color='gray', alpha=0.4, 
                                 lw=1, linestyle='--'))
    
    # Create legend
    legend_elements = [
        mpatches.Rectangle((0, 0), 1, 1, facecolor=colors['entry'], label="Entry/Exit Points"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor=colors['info'], label="Information Nodes"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor=colors['booking'], label="Appointment Booking"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor=colors['management'], label="Appointment Management"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor=colors['success'], label="Success States"),
        mpatches.Rectangle((0, 0), 1, 1, facecolor=colors['error'], label="Error States"),
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    # Set title and formatting
    ax.set_title('Dental Clinic Assistant - Conversation Flow\n(Refactored OOP Architecture)', 
                fontsize=14, fontweight='bold', pad=20)
    ax.set_xlim(-1, 19)
    ax.set_ylim(-3, 11)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Add flow direction indicator
    ax.text(1, 10, 'Flow Direction:', fontsize=10, fontweight='bold')
    ax.text(1, 9.5, '→ Main Flow', fontsize=9)
    ax.text(1, 9.2, '⟶ Back to Main', fontsize=9, alpha=0.6)
    
    plt.tight_layout()
    plt.savefig('simple_dental_flow.png', dpi=200, bbox_inches='tight')
    plt.show()
    
    print("\nFlow Graph Generated Successfully!")
    print("📁 Saved as: simple_dental_flow.png")

if __name__ == "__main__":
    print("Generating Simple Dental Clinic Flow Graph...")
    create_simple_flow_graph()