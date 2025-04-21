import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# --------------------------------------------------------------------------------------------------------
# 1️⃣ Google Sheets Authentication
# --------------------------------------------------------------------------------------------------------

# --- Set Page Configuration ---
st.set_page_config(page_title="CSM Daily Action", page_icon="📌", layout="wide")


# --- Styled Header Box ---
st.markdown(
    """
    <div style='background-color:#0073e6; padding:15px; border-radius:10px; display: flex; align-items: center;'>
        <img src='https://d21xn5q7qjmco5.cloudfront.net/images/logo/1612952677.webp' width='250px' style='margin-left:10px;'>
        <div style='flex-grow:1; text-align:center;'>
            <h1 style='color:white; margin:0;'>CSM DAILY ACTION</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


#----------------------------------------------------------------------------------------------------------
# --- Authenticate using Service Account JSON ------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------




gc = gspread.service_account(filename=r"G:\My Drive\Colab Notebooks\voltaic-mantra-402407-7dfb4640ec7b.json")
spreadsheet = gc.open_by_key("13lD9l0vvEspPtgb-efKch6m5Cjap-5OtyR48XsqZDTs")



# --- Sheet Mapping ---
sheet_mapping = {
    "Open - Complaint - SR": "Complaint-Final",
    "Open Sites": "Open-Sites-Final",
    "Stock Liquidation Project": "Project Stock at Site-Final",
    "Drawing Hold Status": "WCS-Final",
    "FG Status": "FG-Final",
    "Reorder": "Reorder",
    "Appreciation": "Testimonial"
}

# Columns to select for Testimonial sheet only
testimonial_columns = [
    'CSM Names', 'Date', 'Month', 'Id', 'RE Name', 'Zone', 'Customer Name',
    'City', 'Segment', 'Product', 'MSC ID', 'Testimonial Type'
]



# -----------------------------------------------------------------------------------------------------------------
# 2️⃣ Load Data from Google Sheets
# -----------------------------------------------------------------------------------------------------------------

def load_data(sheet_name):
    """Loads only non-empty rows and columns from Google Sheets, with special handling for 'Testimonial'."""
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        data = sheet.get_all_values()

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Remove completely empty rows
        df = df.loc[~df.apply(lambda row: all(cell == "" for cell in row), axis=1)].reset_index(drop=True)

        if df.empty:
            return df

        # Set the first row as header
        df.columns = df.iloc[0].str.strip()
        df = df.drop(0).reset_index(drop=True)

        # Remove completely empty columns
        df = df.dropna(axis=1, how="all")

        # If this is the 'Testimonial' sheet, filter specific columns
        if sheet_name == "Appreciation":
            df = df[[col for col in testimonial_columns if col in df.columns]]

        # Add optional columns if missing
        for col in ["Clearance Date", "Remarks", "Support Required"]:
            if col not in df.columns:
                df[col] = ""

        return df

    except Exception as e:
        st.markdown(f"<p style='font-size:8px; color: red;'>⚠️ Unable to load sheet: {sheet_name}. ({e})</p>", 
                    unsafe_allow_html=True)
        return pd.DataFrame()

# Load all sheets into df_mapping (only where data is present)
df_mapping = {
    key: df for key, sheet in sheet_mapping.items() if not (df := load_data(sheet)).empty
}

# Load Users sheet separately if it has data
df_users = load_data("Users")
df_users = df_users if not df_users.empty else None



# ---------------------------------------------------------------------------------------------------------------------------
# 3️⃣ Login Authentication (CSM, Nation, Master Access)
# ----------------------------------------------------------------------------------------------------------------------------

# --- Initialize Session State (Fixing KeyError) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["logic_id"] = None
    st.session_state["user_type"] = None  # CSM Updated / Nation / All India


# --- Extract Login Data (Based on Selected Type) ---
def get_users_by_type(user_type):
    """Fetch users dynamically based on selected login type."""
    users = set()
    
    if "Drawing Hold Status" in df_mapping:
        wcs_df = df_mapping["Drawing Hold Status"]
        if not wcs_df.empty:
            for _, row in wcs_df.iterrows():
                logic_id = row.get(user_type, "").strip()
                if logic_id:
                    users.add(logic_id)  # Store Logic ID for all user types

    return users    



#----------------------------------------------------------------------------------------------------------
# --- Login Page ---
#----------------------------------------------------------------------------------------------------------
# Ensure session state keys exist
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False



# Apply background image only on the login page
if not st.session_state["authenticated"]:
    page_bg_img = f"""
    <style>
        body {{
            background-image: url("https://www.fenesta.com/images/partner-banner/1674035125_banner.webp");
            background-size: cover;
            background-position: bottom left;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .stApp {{
            background: transparent;
        }}
        .title-box {{
            text-align: center;
            border: 3px solid #2c3e50;  /* Dark Blue Border */
            padding: 10px;
            border-radius: 5px;
            font-size: 26px;
            font-weight: bold;
            color: white;
            background-color: rgba(44, 62, 80, 0.8); /* Dark Blue Box with Transparency */
            display: inline-block;
            width: 100%;
        }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)  # Apply the background image

if not st.session_state["authenticated"]:
    col1, col2, col3 = st.columns([0.25, 0.5, 0.25])  # Center content

    with col2:  # 50% width in the center
        st.markdown('<div class="title-box">🔑 Login to CSM Dashboard</div>', unsafe_allow_html=True)

        user_type = st.selectbox("Select your login type", ["CSM Updated", "Nation", "All India"])
        
        users = get_users_by_type(user_type)
        if not users:
            st.warning("⚠ No users found for the selected type.")

        logic_id = st.text_input("👤 Enter your Logic ID").strip().lower()  # Normalize case

        if st.button("Login"):
            if logic_id == "":
                st.warning("⚠ Please enter a valid Logic ID.")
            elif logic_id in users:
                st.session_state["authenticated"] = True
                st.session_state["logic_id"] = logic_id
                st.session_state["user_type"] = user_type
                st.success(f"✅ Login successful as {user_type}! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Invalid Logic ID. Try again.")

    st.stop()


# If the user is authenticated, show a welcome message without the background image
if st.session_state["authenticated"]:
    st.write(f"Welcome, {st.session_state['logic_id']}!")  


# Ensure session state keys exist
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Apply custom CSS for a very light bluish sidebar
sidebar_style = """
    <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(to bottom, #d0e1f9, #a3c1e3);  /* Very Light Blue Gradient */
            color: black;
        }
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] h4, 
        [data-testid="stSidebar"] h5, 
        [data-testid="stSidebar"] h6, 
        [data-testid="stSidebar"] p {
            color: black;  /* Ensures contrast for readability */
        }
        [data-testid="stSidebar"] button {
            background-color: #8cb3d9 !important;  /* Soft Blue Button */
            color: white !important;
            border-radius: 10px;
            padding: 8px;
            font-size: 16px;
            border: none;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #6f9ac7 !important;  /* Slightly darker blue on hover */
        }
    </style>
"""
st.markdown(sidebar_style, unsafe_allow_html=True)  # Apply the sidebar styling

# --- Sidebar Logout ---
st.sidebar.write(f"✅ Logged in as **{st.session_state['logic_id']}** ({st.session_state['user_type']})")
if st.sidebar.button("🚪 Logout"):
    st.session_state["authenticated"] = False
    st.session_state["logic_id"] = None
    st.session_state["user_type"] = None
    st.rerun()




# ----------------------------------------------------------------------------------------------------------------
# 4️⃣ Tab Selection
# ---------------------------------------------------------------------------------------------------------
if "selected_tab" not in st.session_state:
    st.session_state["selected_tab"] = "Open - Complaint - SR"

tab_names = list(sheet_mapping.keys())

col_list = st.columns(len(tab_names))
for i, tab_name in enumerate(tab_names):
    with col_list[i]:
        if st.button(tab_name, key=f"tab_{i}", use_container_width=True):
            st.session_state["selected_tab"] = tab_name
            st.rerun()



# -------------------------------------------------------------------------------------------
# 5️⃣ Display Data in Table Format (with Sorting & Highlighting)
# -------------------------------------------------------------------------------------------

selected_tab = st.session_state["selected_tab"]
df_selected = df_mapping[selected_tab]

if df_selected.empty:
    st.warning(f"⚠️ No data found for {selected_tab}.")
    st.stop()

# Dynamically select the correct column based on the login type
user_type_column = st.session_state["user_type"]  # "CSM Updated", "Nation", or "All India"
logic_id = st.session_state["logic_id"]

# Ensure the column exists in the DataFrame
if user_type_column not in df_selected.columns:
    st.warning(f"⚠️ Column '{user_type_column}' not found in data for {selected_tab}.")
    st.stop()

# Filter Data based on selected column (CSM Updated / Nation / All India)
filtered_df = df_selected[df_selected[user_type_column] == logic_id]

# st.subheader(f"📝 Update Records for {selected_tab} ({user_type_column})")

if filtered_df.empty:
    st.warning("⚠️ No records assigned to you.")
    st.stop()


#st.dataframe(filtered_df)

st.markdown("---")  # Separator below


# --- Sorting Logic ---

# Mapping for sorting columns
sorting_column = {
    "Open - Complaint - SR": "Ticket Ageing",
    "Open Sites": "Aging",
    "Stock Liquidation Project": "Aging",
    "Drawing Hold Status": "Hold Age",
    "FG Status": "Aging"
}


selected_tab = st.session_state["selected_tab"]
df_selected = df_mapping[selected_tab]

if df_selected.empty:
    st.warning(f"⚠️ No data found for {selected_tab}.")
    st.stop()

# Dynamically select the correct column based on the login type
user_type_column = st.session_state["user_type"]  # "CSM Updated", "Nation", or "All India"
logic_id = st.session_state["logic_id"]

# Ensure the column exists in the DataFrame
if user_type_column not in df_selected.columns:
    st.warning(f"⚠️ Column '{user_type_column}' not found in data for {selected_tab}.")
    st.stop()

#-------------------------------------------------------------------------------------
# --- Place Refresh Button Next to Subheader ---
#------------------------------------------------------------------------------------
# Filter Data based on selected column
filtered_df = df_selected[df_selected[user_type_column] == logic_id]
col1, col2 = st.columns([20, 1])  # Adjust ratio to align properly

with col1:
    st.markdown(f"<h5>📝 Update Records for {selected_tab} ({user_type_column})</h5>", 
                unsafe_allow_html=True)  # h5 makes text smaller

with col2:
    if st.button("🔄", help="Refresh Data", key="refresh_button"):
        df_mapping = {key: load_data(sheet) for key, sheet in sheet_mapping.items()}
        st.session_state["last_refresh"] = pd.Timestamp.now()
        st.rerun()  # Refresh the page




if filtered_df.empty:
    st.warning("⚠️ No records assigned to you.")
    st.stop()

# --- Apply Sorting ---
sort_col = sorting_column.get(selected_tab)

if sort_col and sort_col in filtered_df.columns:
    filtered_df[sort_col] = pd.to_numeric(filtered_df[sort_col], errors="coerce")
    filtered_df = filtered_df.sort_values(by=sort_col, ascending=False)






# --------------------------------------------------------------------------------------------------------------------
# --- Sidebar Filters ------------------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------

st.sidebar.header("Filters")

# --- Nation Dropdown ---
selected_nation = st.sidebar.selectbox("Select Nation", ["All"] + sorted(filtered_df["Nation"].dropna().unique()))

# --- Filter Zones Based on Selected Nation ---
if selected_nation == "All":
    available_zones = sorted(filtered_df["Zone"].dropna().unique())
else:
    available_zones = sorted(filtered_df[filtered_df["Nation"] == selected_nation]["Zone"].dropna().unique())

# --- Zone Dropdown (Filtered Based on Nation) ---
selected_zone = st.sidebar.selectbox("Select Zone", ["All"] + available_zones)

# --- Filter CSMs Based on Selected Zone ---
if selected_zone == "All":
    available_csms = sorted(filtered_df["CSM Updated"].dropna().unique())
else:
    available_csms = sorted(filtered_df[filtered_df["Zone"] == selected_zone]["CSM Updated"].dropna().unique())

# --- CSM Dropdown (Filtered Based on Zone) ---
selected_csm = st.sidebar.selectbox("Select CSM Updated", ["All"] + available_csms)

# --- Apply Selection Without Filtering ---
filtered_df_temp = filtered_df.copy()

# --- Highlight Rows Instead of Filtering ---
def highlight_ageing(row):
    if selected_tab == "Open - Complaint - SR":
        if row["Ticket Ageing"] < 20:
            return ["background-color: lightgreen"] * len(row)
        elif row["Ticket Ageing"] >= 20:
            return ["background-color: lightcoral"] * len(row)
    elif selected_tab == "Open Sites":
        if row["Aging"] < 25:
            return ["background-color: lightgreen"] * len(row)
        elif row["Aging"] >= 25:
            return ["background-color: lightcoral"] * len(row)
    elif selected_tab == "Stock Liquidation Project":
        if row["Aging"] < 25:
            return ["background-color: lightgreen"] * len(row)
        elif row["Aging"] >= 25:
            return ["background-color: lightcoral"] * len(row)
    return [""] * len(row)

#st.dataframe(filtered_df_temp.style.apply(highlight_ageing, axis=1))

#-----------------------------------------------------------------
# --- Sidebar: Summary Counts ---
#-----------------------------------------------------------------
st.sidebar.subheader("📊 Summary Counts")

# Select CSM
selected_csm = st.sidebar.selectbox("Select CSM", filtered_df["CSM Updated"].unique())

# Define sheet names
sheets_to_count = ["Open - Complaint - SR", "Open Sites", "Stock Liquidation Project", "Drawing Hold Status", "FG Status", "Reorder",'Appreciation']

# Count rows for each sheet **only for the selected CSM**
summary_counts = {
    sheet: len(df_mapping[sheet][df_mapping[sheet]["CSM Updated"] == selected_csm]) if sheet in df_mapping else 0
    for sheet in sheets_to_count
}

# Custom CSS to reduce font size
st.sidebar.markdown(
    """
    <style>
        .small-text {
            font-size: 15px !important;
            color: #333; /* Dark grey for better readability */
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display counts in smaller font
for sheet, count in summary_counts.items():
    st.sidebar.markdown(f'<p class="small-text">{sheet}: <b>{count}</b></p>', unsafe_allow_html=True)

# Display last refresh time in smaller font
if "last_refresh" in st.session_state:
    st.sidebar.markdown(
        f'<p class="small-text">Last Refreshed: {st.session_state["last_refresh"].strftime("%Y-%m-%d %H:%M:%S")}</p>',
        unsafe_allow_html=True,
    )




#---------------------------------------------------------------------------
# --- Apply Header Styling ---
#---------------------------------------------------------------------------

def color_headers(s):
    return ['background-color: lightblue; color: black; font-weight: bold' for _ in s]

styled_df = filtered_df_temp.style.set_table_styles(
    [{'selector': 'thead th',
      'props': [('background-color', 'darkblue'), 
                ('color', 'white'), 
                ('font-weight', 'bold'),
                ('text-align', 'center')]}]
).apply(color_headers, axis=0)

# --- Display Final Filtered Data ---
#st.dataframe(styled_df)



#-----------------------------------------------------------------------------
# --- Editable Columns ---
#-----------------------------------------------------------------------------

# Define editable columns
editable_columns = ["Clearance Date", "Remarks", "Support Required"]
filtered_df["Clearance Date"] = pd.to_datetime(filtered_df["Clearance Date"], errors="coerce").dt.date

df_display = filtered_df.copy()

df_display["Clearance Date"] = pd.to_datetime(df_display["Clearance Date"], errors="coerce").dt.date
df_display = filtered_df.iloc[:,3:]


# Streamlit UI
# st.title("Ticket Management System")

# Dropdown for selecting tabs
# selected_tab = st.selectbox("Select a tab", ["Open - Complaint - SR", "Open Sites", "Stock Liquidation Project"])

def highlight_rows(row):
    highlight_color = ""
    if selected_tab == "Open - Complaint - SR":
        if row["Ticket Ageing"] < 20:
            highlight_color = "background-color: lightgreen"
        elif row["Ticket Ageing"] >= 20:
            highlight_color = "background-color: lightcoral"
    elif selected_tab == "Open Sites":
        if row["Aging"] < 25:
            highlight_color = "background-color: lightgreen"
        elif row["Aging"] >= 25:
            highlight_color = "background-color: lightcoral"
    elif selected_tab == "Stock Liquidation Project":
        if row["Aging"] < 25:
            highlight_color = "background-color: lightgreen"
        elif row["Aging"] >= 25:
            highlight_color = "background-color: lightcoral"
    
    return [highlight_color if col not in editable_columns else "" for col in row.index]

# Apply color formatting
df_display = df_display.style.apply(highlight_rows, axis=1)

# Editable DataFrame
edited_df = st.data_editor(
    df_display,
    column_config={
        "Clearance Date": st.column_config.DateColumn(
            "Clearance Date",
            min_value=datetime.today().date()
        ),
        "Remarks": st.column_config.TextColumn("Remarks"),
        "Support Required": st.column_config.TextColumn("Support Required"),
    },
    disabled=[col for col in filtered_df.columns if col not in editable_columns],
    hide_index=True,
)


# ---------------------------------------------------------------------------------------------
# 6️⃣ Save Updated Data
# ---------------------------------------------------------------------------------------------
def save_to_google_sheet(df, selected_tab):
    try:
        # Convert all datetime columns to string format to avoid serialization errors
        df = df.astype(str)

        # Define explicit mapping of tabs to their corresponding "Clear" sheets
        clear_sheet_mapping = {
            "Complaint File": "Complaint Clear",
            "Open Sites Final": "Open SitesClear",
            "Project Stock at Site-Final": "Project Stock at Site-Clear",
            "WCS-Final": "WCS Clear",
            "FG-Final":"FG Clear",
            "Reorder":"Reorder Clear"

        }

        # Get the correct "Clear" sheet name based on the selected tab
        clear_sheet_name = clear_sheet_mapping.get(selected_tab, f"{selected_tab} Clear")  # Default fallback

        # Access or Create the Target Sheet
        try:
            sheet = spreadsheet.worksheet(clear_sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=clear_sheet_name, rows=str(df.shape[0]), cols=str(df.shape[1]))

        # Update Google Sheet with cleaned data
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

        st.success(f"✅ Data successfully saved to '{clear_sheet_name}' sheet.")
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")

# --- Save Button ---
if st.button("💾 Save Data"):
    save_to_google_sheet(edited_df, selected_tab)  


# Save the selected tab's data to the relevant "Clear" sheet     modify this code with the main google sheet with the file path "G:\Shared drives\list 10\All_Sheets.xlsx"