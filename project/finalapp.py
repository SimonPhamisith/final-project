#!/usr/bin/env python
# coding: utf-8

# In[34]:


import streamlit as st
import pandas as pd
import plotly.express as px
import re

excel_file_path = 'JTM_inbound_20240902eng.xlsx'
excel_file = pd.ExcelFile(excel_file_path)
sheet_names = excel_file.sheet_names  # This gives us a list of available sheets


# ## merged dataset(copy pasted from my final project)

# In[33]:


# Load the 'Grand Total' sheet from the Excel file
grand_total_df = pd.read_excel(excel_file_path, sheet_name='Grand Total')
# Remove unnecessary rows and select the relevant columns
grand_total_df_cleaned = grand_total_df.iloc[2:, :2]  # Start from row 3 and use the first two columns
grand_total_df_cleaned.columns = ['Month_Year', 'Visitor Arrivals'] 


# Clean 'Month_Year' column by removing any special characters and parsing the date
grand_total_df_cleaned['Month_Year'] = grand_total_df_cleaned['Month_Year'].apply(lambda x: re.sub(r'[^A-Za-z0-9\s]', '', str(x)))
grand_total_df_cleaned['Month_Year'] = pd.to_datetime(grand_total_df_cleaned['Month_Year'], errors='coerce', format='%Y %b')

# Drop rows with missing dates or invalid formats
grand_total_df_cleaned.dropna(subset=['Month_Year'], inplace=True)

# Convert 'Visitor Arrivals' to numeric and drop missing data
grand_total_df_cleaned['Visitor Arrivals'] = pd.to_numeric(grand_total_df_cleaned['Visitor Arrivals'], errors='coerce')
grand_total_df_cleaned.dropna(inplace=True)
# Load the CSV data file
csv_data_file_path = 'API_ST.INT.ARVL_DS2_en_csv_v2_32045.csv'
csv_data = pd.read_csv(csv_data_file_path, skiprows=3)
japan_data = csv_data[csv_data['Country Name'] == 'Japan']

# Drop unnecessary columns
japan_data_cleaned = japan_data.drop(columns=['Country Code', 'Indicator Name', 'Indicator Code', 'Unnamed: 68'])

# Transpose the data so that years become rows
japan_data_cleaned = japan_data_cleaned.set_index('Country Name').transpose().reset_index()
japan_data_cleaned.columns = ['Year', 'Visitor Arrivals']  # Rename columns for clarity

# Convert 'Year' to datetime and handle missing values
japan_data_cleaned['Year'] = pd.to_datetime(japan_data_cleaned['Year'], format='%Y', errors='coerce')
japan_data_cleaned['Visitor Arrivals'] = pd.to_numeric(japan_data_cleaned['Visitor Arrivals'], errors='coerce')
japan_data_cleaned.dropna(inplace=True)
# Concatenate the cleaned monthly and annual data
merged_data = pd.concat([japan_data_cleaned, grand_total_df_cleaned], ignore_index=True).sort_values(by='Year')

# Reset the index
merged_data.reset_index(drop=True, inplace=True)



# In[44]:


# Function to load and clean data
@st.cache
def load_data():
    # Load the Excel data
    excel_file_path = 'JTM_inbound_20240902eng.xlsx'
    grand_total_df = pd.read_excel(excel_file_path, sheet_name='Grand Total')
    grand_total_df_cleaned = grand_total_df.iloc[2:, :2]
    grand_total_df_cleaned.columns = ['Month_Year', 'Visitor Arrivals']
    grand_total_df_cleaned['Month_Year'] = grand_total_df_cleaned['Month_Year'].apply(lambda x: re.sub(r'[^A-Za-z0-9\s]', '', str(x)))
    grand_total_df_cleaned['Month_Year'] = pd.to_datetime(grand_total_df_cleaned['Month_Year'], errors='coerce', format='%Y %b')
    grand_total_df_cleaned.dropna(subset=['Month_Year'], inplace=True)
    grand_total_df_cleaned['Visitor Arrivals'] = pd.to_numeric(grand_total_df_cleaned['Visitor Arrivals'], errors='coerce')
    grand_total_df_cleaned.dropna(inplace=True)

    # Load and clean CSV data
    csv_data_file_path = 'API_ST.INT.ARVL_DS2_en_csv_v2_32045.csv'
    csv_data = pd.read_csv(csv_data_file_path, skiprows=3)
    japan_data = csv_data[csv_data['Country Name'] == 'Japan']
    japan_data_cleaned = japan_data.drop(columns=['Country Code', 'Indicator Name', 'Indicator Code', 'Unnamed: 68'])
    japan_data_cleaned = japan_data_cleaned.set_index('Country Name').transpose().reset_index()
    japan_data_cleaned.columns = ['Year', 'Visitor Arrivals']
    japan_data_cleaned['Year'] = pd.to_datetime(japan_data_cleaned['Year'], format='%Y', errors='coerce')
    japan_data_cleaned['Visitor Arrivals'] = pd.to_numeric(japan_data_cleaned['Visitor Arrivals'], errors='coerce')
    japan_data_cleaned.dropna(inplace=True)

    # Load additional CSV files
    regional_data = pd.read_csv('regional.csv')
    purpose_data = pd.read_csv('purpose.csv')
    country_data = pd.read_csv('country.csv')

    # Merge data
    merged_data = pd.concat([grand_total_df_cleaned, japan_data_cleaned], ignore_index=True).sort_values(by='Month_Year')
    merged_data.reset_index(drop=True, inplace=True)

    return merged_data, regional_data, purpose_data, country_data

# Load the data
data, regional_data, purpose_data, country_data = load_data()


# In[ ]:





# ## set up streamlit

# In[45]:


# Streamlit title and filters
st.title('Tourism Data Visualization for Japan')
years = pd.to_datetime(data['Month_Year']).dt.year.dropna().unique()  # Ensure no NaN values and unique years
year_filter = st.sidebar.multiselect('Select Year(s)', options=years, default=[years[-1]] if years.size > 0 else [])

# Filter data based on user selection
filtered_data = data[data['Month_Year'].dt.year.isin(year_filter)]
filtered_country_data = country_data[country_data['Year'].isin(year_filter)]

# Plotting the data
fig = px.line(filtered_data, x='Month_Year', y='Visitor Arrivals', title='Visitor Arrivals to Japan Over Time')
st.plotly_chart(fig)



# In[46]:


# Visualization for regional data
fig_regional = px.bar(regional_data, x='Prefecture', y='Visit Rate(%)', title='Visitation Rates by Prefecture')
st.plotly_chart(fig_regional)


# In[47]:


# Visualization for purpose of visit
purpose_data['Year'] = pd.to_datetime(purpose_data['Year']).dt.year  # Ensure 'Year' is in datetime format


# In[48]:


# Aggregate data by year and purpose
purpose_agg = purpose_data.groupby(['Year', 'Purpose_of_visit_to_Japan']).sum().reset_index()


# In[52]:


# Visualization for arrivals by country
fig_country = px.bar(filtered_country_data, x='Country/Area(23 Markets)', y='Visitor Arrivals', title='Visitor Arrivals by Country')
st.plotly_chart(fig_country)
# Convert 'Visitor Arrivals' to numeric, handling any non-numeric issues
country_data['Visitor Arrivals'] = pd.to_numeric(country_data['Visitor Arrivals'].str.replace(',', ''), errors='coerce')


# In[53]:


data = {
    'Year': ['2018', '2019', '2020', '2021', '2022'],
    'Visitor Arrivals': [20e6, 30e6, 5e6, 10e6, 25e6],
    'Purpose': ['Tourism', 'Business', 'Tourism', 'Business', 'Tourism']
}
df = pd.DataFrame(data)
df['Year'] = pd.to_datetime(df['Year']).dt.year  # converting to datetime

# Streamlit App Title
st.title('Tourism Data Visualization for Japan')

# Line Chart for Visitor Arrivals Over Time with Events
st.header("Visitor Arrivals to Japan Over Time with Key Events")

# Line Chart: Visitor Arrivals
fig = px.line(df, x='Year', y='Visitor Arrivals', title='Visitor Arrivals to Japan (2018-2022)')

# Adding event annotations to the line chart
events = {'2018': 'Visa Policy Relaxation', '2020': 'COVID-19 Pandemic', '2021': 'Tokyo Olympics'}
for year, event in events.items():
    fig.add_annotation(x=year, y=df[df['Year'] == int(year)]['Visitor Arrivals'].max(),
                       text=event, showarrow=True, arrowhead=1, arrowsize=2, arrowwidth=2, arrowcolor="#636efa")

# Display the Line Chart in Streamlit
st.plotly_chart(fig)

# Stacked Bar Chart for Purpose of Visit
st.header("Visitor Arrivals by Purpose of Visit")

# Stacked Bar Chart: Purpose of Visit
fig_purpose = px.bar(df, x='Year', y='Visitor Arrivals', color='Purpose',
                     title='Visitor Arrivals to Japan by Purpose of Visit (2018-2022)')
fig_purpose.update_layout(barmode='stack')

# Display the Stacked Bar Chart in Streamlit
st.plotly_chart(fig_purpose)


# In[ ]:





# In[ ]:




