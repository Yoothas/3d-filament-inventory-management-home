import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
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

@st.cache_data(show_spinner=False)
def load_filaments() -> List[Dict[str, Any]]:
    """Load filaments from JSON file"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else data.get('filaments', [])
    return []

def save_filaments(filaments: List[Dict[str, Any]]) -> None:
    """Save filaments to JSON file"""
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(filaments, f, indent=2)
    load_filaments.clear()

def calculate_stats(filaments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate inventory statistics"""
    if not filaments:
        return {
            'total_spools': 0,
            'total_weight': 0,
            'remaining_weight': 0,
            'total_value': 0,
            'low_stock_count': 0
        }
    
    total_weight = sum(f.get('weight') or 0 for f in filaments)
    remaining_weight = sum(f.get('remainingWeight') or 0 for f in filaments)

    total_value = 0
    low_stock = 0
    for filament in filaments:
        weight = filament.get('weight') or 0
        remaining = filament.get('remainingWeight') or 0
        if weight > 0:
            total_value += (filament.get('cost', 0) or 0) * (remaining / weight)
            if (remaining / weight) < 0.2:
                low_stock += 1
    
    return {
        'total_spools': len(filaments),
        'total_weight': total_weight,
        'remaining_weight': remaining_weight,
        'total_value': total_value,
        'low_stock_count': low_stock
    }

def format_filament_card(filament: Dict[str, Any]) -> str:
    """Create a formatted card for a filament"""
    total_weight = filament.get('weight') or 0
    remaining_weight = filament.get('remainingWeight') or 0

    if total_weight > 0:
        remaining_pct = max(min((remaining_weight / total_weight) * 100, 100), 0)
    else:
        remaining_pct = 0

    is_low_stock = total_weight > 0 and remaining_pct < 20
    
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


def remaining_ratio(filament: Dict[str, Any]) -> float:
    """Return remaining weight ratio between 0 and 1."""
    weight = filament.get('weight') or 0
    if weight <= 0:
        return 0.0
    remaining = filament.get('remainingWeight') or 0
    # Clamp to keep charts sane if the numbers drift slightly
    return max(min(remaining / weight, 1.0), 0.0)


def used_weight(filament: Dict[str, Any]) -> float:
    """Calculate weight used from a filament."""
    weight = filament.get('weight') or 0
    remaining = filament.get('remainingWeight') or 0
    return max(weight - remaining, 0)


def filter_filaments(
    all_filaments: List[Dict[str, Any]],
    view_mode: str,
    selected_material: str,
    selected_brand: str,
    search_query: str,
    low_stock_only: bool
) -> List[Dict[str, Any]]:
    """Filter filaments based on criteria."""
    filtered = []
    search_lower = (search_query or '').lower()

    for filament in all_filaments:
        is_archived = filament.get('archived', False)

        if view_mode == "Active Spools" and is_archived:
            continue
        if view_mode == "Archived Spools" and not is_archived:
            continue

        if selected_material != "All" and filament.get('material') != selected_material:
            continue

        if selected_brand != "All" and filament.get('brand') != selected_brand:
            continue

        if search_lower:
            haystack = " ".join([
                str(filament.get('brand', '')),
                str(filament.get('material', '')),
                str(filament.get('color', '')),
                str(filament.get('notes', ''))
            ]).lower()
            if search_lower not in haystack:
                continue

        if low_stock_only and remaining_ratio(filament) >= 0.2:
            continue

        filtered.append(filament)

    return filtered


def sort_filaments(filaments: List[Dict[str, Any]], sort_key: str) -> List[Dict[str, Any]]:
    """Sort filaments based on the specified key."""
    if not filaments:
        return filaments

    if sort_key == "lastUsed":
        # Sort by most recent activity (either lastUsed or updatedAt)
        # This treats manual weight adjustments as "recent activity"
        def get_most_recent_activity(fil: Dict[str, Any]) -> str:
            last_used = fil.get('lastUsed') or ''
            updated_at = fil.get('updatedAt') or ''
            # Return the most recent timestamp between lastUsed and updatedAt
            return max(last_used, updated_at) if last_used and updated_at else (last_used or updated_at)
        
        return sorted(filaments, key=get_most_recent_activity, reverse=True)
    if sort_key == "usage":
        return sorted(filaments, key=lambda x: used_weight(x), reverse=True)
    if sort_key == "usage_asc":
        return sorted(filaments, key=lambda x: used_weight(x))
    if sort_key == "stock_low":
        return sorted(filaments, key=lambda x: remaining_ratio(x))
    if sort_key == "stock_high":
        return sorted(filaments, key=lambda x: remaining_ratio(x), reverse=True)
    if sort_key == "purchase_new":
        return sorted(filaments, key=lambda x: x.get('purchaseDate') or '1970-01-01', reverse=True)
    if sort_key == "purchase_old":
        return sorted(filaments, key=lambda x: x.get('purchaseDate') or '1970-01-01')
    if sort_key == "brand":
        return sorted(filaments, key=lambda x: x.get('brand') or '')
    if sort_key == "brand_desc":
        return sorted(filaments, key=lambda x: x.get('brand') or '', reverse=True)
    if sort_key == "material":
        return sorted(filaments, key=lambda x: x.get('material') or '')
    if sort_key == "color":
        return sorted(filaments, key=lambda x: x.get('color') or '')
    if sort_key == "cost_desc":
        return sorted(filaments, key=lambda x: x.get('cost') or 0, reverse=True)
    if sort_key == "cost":
        return sorted(filaments, key=lambda x: x.get('cost') or 0)

    return filaments

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
    
    active_filaments = [f for f in all_filaments if not f.get('archived', False)]
    archived_filaments = [f for f in all_filaments if f.get('archived', False)]
    stats = calculate_stats(active_filaments)
    
    # Material filter
    materials = sorted({f.get('material') for f in all_filaments if f.get('material')})  # type: ignore
    selected_material = st.sidebar.selectbox("Filter by Material", ["All"] + materials)
    
    # Brand filter
    brands = sorted({f.get('brand') for f in all_filaments if f.get('brand')})  # type: ignore
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
    
    sort_key = sort_options[selected_sort]
    filtered_filaments = sort_filaments(
        filter_filaments(
            all_filaments,
            view_mode,
            selected_material,
            selected_brand,
            search_query,
            show_low_stock_only
        ),
        sort_key
    )
    
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
            df['stock_pct'] = df.apply(remaining_ratio, axis=1) * 100
            df['label'] = df['brand'].fillna('') + ' ' + df['color'].fillna('')

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
                remaining_pct = remaining_ratio(filament) * 100
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
            new_weight = st.number_input("Original Weight (g) *", min_value=1, value=1000)
            new_remaining = st.number_input("Remaining Weight (g) *", min_value=0, value=1000, max_value=new_weight)
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
                
                all_filaments.append(new_filament)
                save_filaments(all_filaments)
                st.success("✅ Filament added successfully!")
                st.rerun()
            else:
                st.error("❌ Please fill in all required fields (marked with *)")

if __name__ == "__main__":
    main()
