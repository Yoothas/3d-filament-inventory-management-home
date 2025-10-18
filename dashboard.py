import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="3D Filament Inventory",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .low-stock {
        background-color: #ffebee;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #f44336;
    }
    .metric-card {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Data file path
DATA_FILE = Path(__file__).parent / 'data' / 'filaments.json'

@st.cache_data
def load_filaments():
    """Load filaments from JSON file"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('filaments', [])
    return []

def save_filaments(filaments):
    """Save filaments to JSON file"""
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(filaments, f, indent=2)
    st.cache_data.clear()

def calculate_stats(filaments):
    """Calculate inventory statistics"""
    if not filaments:
        return {
            'total_spools': 0,
            'total_weight': 0,
            'remaining_weight': 0,
            'total_value': 0,
            'low_stock_count': 0
        }
    
    total_weight = sum(f['weight'] for f in filaments)
    remaining_weight = sum(f['remainingWeight'] for f in filaments)
    total_value = sum(f.get('cost', 0) * (f['remainingWeight'] / f['weight']) for f in filaments)
    low_stock = sum(1 for f in filaments if (f['remainingWeight'] / f['weight']) < 0.2)
    
    return {
        'total_spools': len(filaments),
        'total_weight': total_weight,
        'remaining_weight': remaining_weight,
        'total_value': total_value,
        'low_stock_count': low_stock
    }

def format_filament_card(filament):
    """Create a formatted card for a filament"""
    remaining_pct = (filament['remainingWeight'] / filament['weight']) * 100
    is_low_stock = remaining_pct < 20
    
    card_class = 'low-stock' if is_low_stock else ''
    
    return f"""
    <div class="{card_class}" style="margin-bottom: 10px;">
        <h4>🎨 {filament['color']} - {filament['material']}</h4>
        <p><strong>Brand:</strong> {filament['brand']}</p>
        <p><strong>Remaining:</strong> {filament['remainingWeight']}g / {filament['weight']}g ({remaining_pct:.1f}%)</p>
        <p><strong>Diameter:</strong> {filament['diameter']}mm</p>
        <p><strong>Cost:</strong> ${filament.get('cost', 0):.2f}</p>
        {f"<p><strong>Purchase Date:</strong> {filament.get('purchaseDate', 'N/A')}</p>" if filament.get('purchaseDate') else ''}
    </div>
    """

# Main app
def main():
    st.title("🎯 3D Filament Inventory Dashboard")
    
    # Load data
    all_filaments = load_filaments()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters & Sorting")
    
    # Archive filter (NEW)
    view_mode = st.sidebar.radio(
        "📦 View Mode",
        options=["Active Spools", "Archived Spools", "All Spools"],
        index=0
    )
    
    # Filter by archived status
    if view_mode == "Active Spools":
        filaments = [f for f in all_filaments if not f.get('archived', False)]
    elif view_mode == "Archived Spools":
        filaments = [f for f in all_filaments if f.get('archived', False)]
    else:  # All Spools
        filaments = all_filaments
    
    # Calculate stats (only active spools)
    active_filaments = [f for f in all_filaments if not f.get('archived', False)]
    archived_filaments = [f for f in all_filaments if f.get('archived', False)]
    stats = calculate_stats(active_filaments)
    
    # Material filter
    materials = sorted(set(f['material'] for f in filaments)) if filaments else []
    selected_material = st.sidebar.selectbox("Filter by Material", ["All"] + materials)
    
    # Brand filter
    brands = sorted(set(f['brand'] for f in filaments)) if filaments else []
    selected_brand = st.sidebar.selectbox("Filter by Brand", ["All"] + brands)
    
    # Search
    search_query = st.sidebar.text_input("🔎 Search", "")
    
    # Sort options
    sort_options = {
        "Recently Used": "lastUsed",
        "Most Used": "usage",
        "Least Used": "usage_asc",
        "Low Stock First": "stock_low",
        "High Stock First": "stock_high",
        "Newest Purchase": "purchase_new",
        "Oldest Purchase": "purchase_old",
        "Brand (A-Z)": "brand",
        "Brand (Z-A)": "brand_desc",
        "Material": "material",
        "Color (A-Z)": "color",
        "Cost (High-Low)": "cost_desc",
        "Cost (Low-High)": "cost"
    }
    
    selected_sort = st.sidebar.selectbox("📊 Sort by", list(sort_options.keys()))
    
    # Show low stock only toggle
    show_low_stock_only = st.sidebar.checkbox("⚠️ Show Low Stock Only", False)
    
    # Auto-Archive button
    st.sidebar.divider()
    if st.sidebar.button("🗄️ Auto-Archive Empty Spools"):
        archived_count = 0
        archived_names = []
        for filament in all_filaments:
            if filament['remainingWeight'] <= 0 and not filament.get('archived', False):
                filament['archived'] = True
                filament['archivedAt'] = datetime.now().isoformat()
                filament['updatedAt'] = datetime.now().isoformat()
                archived_count += 1
                archived_names.append(f"{filament['brand']} {filament['color']}")
        
        if archived_count > 0:
            save_filaments(all_filaments)
            st.sidebar.success(f"Archived {archived_count} spool(s)!")
            st.rerun()
        else:
            st.sidebar.info("No empty spools to archive")
    
    # Statistics cards
    st.header("📊 Inventory Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Active Spools", stats['total_spools'])
    with col2:
        st.metric("Archived Spools", len(archived_filaments))
    with col3:
        st.metric("Total Weight", f"{stats['total_weight']:.0f}g")
    with col4:
        st.metric("Remaining", f"{stats['remaining_weight']:.0f}g")
    with col5:
        st.metric("⚠️ Low Stock", stats['low_stock_count'])
    
    # Filter filaments
    filtered_filaments = filaments.copy()
    
    if selected_material != "All":
        filtered_filaments = [f for f in filtered_filaments if f['material'] == selected_material]
    
    if selected_brand != "All":
        filtered_filaments = [f for f in filtered_filaments if f['brand'] == selected_brand]
    
    if search_query:
        query_lower = search_query.lower()
        filtered_filaments = [
            f for f in filtered_filaments 
            if query_lower in f['brand'].lower() 
            or query_lower in f['material'].lower() 
            or query_lower in f['color'].lower()
        ]
    
    if show_low_stock_only:
        filtered_filaments = [
            f for f in filtered_filaments 
            if (f['remainingWeight'] / f['weight']) < 0.2
        ]
    
    # Sort filaments
    sort_key = sort_options[selected_sort]
    
    if sort_key == "lastUsed":
        filtered_filaments.sort(
            key=lambda x: x.get('lastUsed', '1970-01-01'), 
            reverse=True
        )
    elif sort_key == "usage":
        filtered_filaments.sort(
            key=lambda x: x['weight'] - x['remainingWeight'], 
            reverse=True
        )
    elif sort_key == "usage_asc":
        filtered_filaments.sort(
            key=lambda x: x['weight'] - x['remainingWeight']
        )
    elif sort_key == "stock_low":
        filtered_filaments.sort(
            key=lambda x: x['remainingWeight'] / x['weight']
        )
    elif sort_key == "stock_high":
        filtered_filaments.sort(
            key=lambda x: x['remainingWeight'] / x['weight'], 
            reverse=True
        )
    elif sort_key == "purchase_new":
        filtered_filaments.sort(
            key=lambda x: x.get('purchaseDate', '1970-01-01'), 
            reverse=True
        )
    elif sort_key == "purchase_old":
        filtered_filaments.sort(
            key=lambda x: x.get('purchaseDate', '1970-01-01')
        )
    elif sort_key == "brand":
        filtered_filaments.sort(key=lambda x: x['brand'])
    elif sort_key == "brand_desc":
        filtered_filaments.sort(key=lambda x: x['brand'], reverse=True)
    elif sort_key == "material":
        filtered_filaments.sort(key=lambda x: x['material'])
    elif sort_key == "color":
        filtered_filaments.sort(key=lambda x: x['color'])
    elif sort_key == "cost_desc":
        filtered_filaments.sort(key=lambda x: x.get('cost', 0), reverse=True)
    elif sort_key == "cost":
        filtered_filaments.sort(key=lambda x: x.get('cost', 0))
    
    # Charts
    if filtered_filaments:
        st.header("📈 Visualizations")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Material distribution pie chart
            df = pd.DataFrame(filtered_filaments)
            material_counts = df['material'].value_counts()
            fig = px.pie(
                values=material_counts.values, 
                names=material_counts.index,
                title="Material Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            # Stock levels bar chart
            df['stock_pct'] = (df['remainingWeight'] / df['weight'] * 100).round(1)
            df['label'] = df['brand'] + ' ' + df['color']
            
            fig = px.bar(
                df.head(10), 
                x='label', 
                y='stock_pct',
                title="Stock Levels (Top 10)",
                labels={'label': 'Filament', 'stock_pct': 'Stock %'},
                color='stock_pct',
                color_continuous_scale=['red', 'yellow', 'green']
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Filament list
    st.header(f"🎨 Filaments ({len(filtered_filaments)})")
    
    if not filtered_filaments:
        st.info("No filaments found. Add your first spool to get started!")
    else:
        # Display in columns
        cols = st.columns(3)
        for idx, filament in enumerate(filtered_filaments):
            with cols[idx % 3]:
                remaining_pct = (filament['remainingWeight'] / filament['weight']) * 100
                is_low_stock = remaining_pct < 20
                
                with st.container():
                    if is_low_stock:
                        st.error(f"⚠️ Low Stock!")
                    
                    st.subheader(f"🎨 {filament['color']}")
                    st.write(f"**Material:** {filament['material']}")
                    st.write(f"**Brand:** {filament['brand']}")
                    st.write(f"**Diameter:** {filament['diameter']}mm")
                    
                    # Progress bar
                    st.progress(remaining_pct / 100)
                    st.write(f"**Remaining:** {filament['remainingWeight']}g / {filament['weight']}g ({remaining_pct:.1f}%)")
                    
                    if filament.get('cost'):
                        st.write(f"**Cost:** ${filament['cost']:.2f}")
                    
                    if filament.get('purchaseDate'):
                        st.write(f"**Purchase:** {filament['purchaseDate']}")
                    
                    # Check if in edit mode
                    is_archived = filament.get('archived', False)
                    editing_key = f'editing_{filament["id"]}'
                    is_editing = st.session_state.get(editing_key, False)
                    
                    if is_editing:
                        # Show edit form
                        with st.form(key=f"edit_form_{filament['id']}"):
                            edit_brand = st.text_input("Brand", value=filament['brand'])
                            edit_color = st.text_input("Color", value=filament['color'])
                            edit_material = st.selectbox(
                                "Material", 
                                ["PLA", "ABS", "PETG", "TPU", "ASA", "Other"],
                                index=["PLA", "ABS", "PETG", "TPU", "ASA", "Other"].index(filament['material']) if filament['material'] in ["PLA", "ABS", "PETG", "TPU", "ASA", "Other"] else 0
                            )
                            edit_weight = st.number_input("Original Weight (g)", value=float(filament['weight']), min_value=0.0)
                            edit_remaining = st.number_input("Remaining Weight (g)", value=float(filament['remainingWeight']), min_value=0.0)
                            edit_diameter = st.selectbox(
                                "Diameter (mm)", 
                                [1.75, 2.85, 3.0],
                                index=[1.75, 2.85, 3.0].index(filament['diameter']) if filament['diameter'] in [1.75, 2.85, 3.0] else 0
                            )
                            edit_cost = st.number_input("Cost ($)", value=float(filament.get('cost', 0)), min_value=0.0, step=0.01)
                            edit_notes = st.text_area("Notes", value=filament.get('notes', ''))
                            
                            save_col, cancel_col = st.columns(2)
                            with save_col:
                                save_clicked = st.form_submit_button("💾 Save")
                            with cancel_col:
                                cancel_clicked = st.form_submit_button("❌ Cancel")
                            
                            if save_clicked:
                                # Update filament
                                filament['brand'] = edit_brand
                                filament['color'] = edit_color
                                filament['material'] = edit_material
                                filament['weight'] = edit_weight
                                filament['remainingWeight'] = edit_remaining
                                filament['diameter'] = edit_diameter
                                filament['cost'] = edit_cost
                                filament['notes'] = edit_notes
                                filament['updatedAt'] = datetime.now().isoformat()
                                
                                save_filaments(all_filaments)
                                st.session_state[editing_key] = False
                                st.success("✅ Updated successfully!")
                                st.rerun()
                            
                            if cancel_clicked:
                                st.session_state[editing_key] = False
                                st.rerun()
                    else:
                        # Show action buttons
                        button_col1, button_col2, button_col3 = st.columns(3)
                        
                        with button_col1:
                            if st.button("✏️ Edit", key=f"edit_{filament['id']}"):
                                st.session_state[editing_key] = True
                                st.rerun()
                        
                        with button_col2:
                            if is_archived:
                                if st.button("↻ Restore", key=f"unarchive_{filament['id']}"):
                                    filament['archived'] = False
                                    if 'archivedAt' in filament:
                                        del filament['archivedAt']
                                    filament['updatedAt'] = datetime.now().isoformat()
                                    save_filaments(all_filaments)
                                    st.success(f"Restored {filament['brand']} {filament['color']}")
                                    st.rerun()
                            else:
                                if filament['remainingWeight'] <= 0:
                                    if st.button("📦 Archive", key=f"archive_{filament['id']}"):
                                        filament['archived'] = True
                                        filament['archivedAt'] = datetime.now().isoformat()
                                        filament['updatedAt'] = datetime.now().isoformat()
                                        save_filaments(all_filaments)
                                        st.success(f"Archived {filament['brand']} {filament['color']}")
                                        st.rerun()
                        
                        with button_col3:
                            if st.button("🗑️ Delete", key=f"delete_{filament['id']}"):
                                all_filaments.remove(filament)
                                save_filaments(all_filaments)
                                st.success("Deleted successfully!")
                                st.rerun()
                        
                        # Show archived badge
                        if is_archived:
                            st.info(f"📦 Archived on {filament.get('archivedAt', 'Unknown')[:10]}")
                    
                    st.divider()
    
    # Add new filament section
    st.header("➕ Add New Filament")
    
    with st.form("add_filament_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_brand = st.text_input("Brand *", "")
            new_material = st.selectbox("Material *", ["PLA", "ABS", "PETG", "TPU", "ASA", "Other"])
            new_color = st.text_input("Color *", "")
        
        with col2:
            new_weight = st.number_input("Original Weight (g) *", min_value=0, value=1000)
            new_remaining = st.number_input("Remaining Weight (g) *", min_value=0, value=1000)
            new_diameter = st.selectbox("Diameter (mm) *", [1.75, 2.85, 3.0])
        
        with col3:
            new_cost = st.number_input("Cost ($)", min_value=0.0, value=19.95, step=0.01)
            new_purchase_date = st.date_input("Purchase Date")
            new_notes = st.text_area("Notes")
        
        submitted = st.form_submit_button("➕ Add Filament")
        
        if submitted:
            if new_brand and new_material and new_color:
                new_filament = {
                    'id': str(int(datetime.now().timestamp() * 1000)),
                    'brand': new_brand,
                    'material': new_material,
                    'color': new_color,
                    'weight': new_weight,
                    'remainingWeight': new_remaining,
                    'diameter': new_diameter,
                    'cost': new_cost,
                    'purchaseDate': str(new_purchase_date),
                    'notes': new_notes,
                    'createdAt': datetime.now().isoformat()
                }
                
                filaments.append(new_filament)
                save_filaments(filaments)
                st.success("✅ Filament added successfully!")
                st.rerun()
            else:
                st.error("❌ Please fill in all required fields (marked with *)")

if __name__ == "__main__":
    main()
