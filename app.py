from flask import Flask, render_template, jsonify, request
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import plotly.utils
import numpy as np
from datetime import datetime

app = Flask(__name__)

df = pd.read_csv('data/donors.csv', low_memory=False)

df[' Gift $ '] = df[' Gift $ '].str.replace('$', '').str.replace(',', '').str.strip()
df[' Gift $ '] = pd.to_numeric(df[' Gift $ '], errors='coerce')
df = df.dropna(subset=['X', 'Y', ' Gift $ '])

df['State'] = df['State'].fillna(df['Region Abbreviation'])
df['City'] = df['City.1'].fillna(df['City']).fillna(df['ARC Best City'])
df['ZIP'] = df['ZIP'].fillna(df['ARC Best Zip']).fillna(df['Postal'])

df['Gift_Category'] = pd.cut(df[' Gift $ '], 
                              bins=[0, 5000, 7500, 10000, 15000, 25000, 50000, 100000, float('inf')],
                              labels=['$5K', '$5K-7.5K', '$7.5K-10K', '$10K-15K', '$15K-25K', '$25K-50K', '$50K-100K', '>$100K'])

state_counts = df.groupby('State').size().to_dict()
df['State_Donors'] = df['State'].map(state_counts)

RED_CROSS_COLORS = {
    'primary_red': '#ED1B2E',
    'secondary_red': '#B31E29',
    'dark_red': '#8B1A1E',
    'gray': '#6D6E70',
    'light_gray': '#D7D7D8',
    'white': '#FFFFFF',
    'black': '#231F20'
}

GIFT_COLORS = {
    '$5K': '#FFE6E8',
    '$5K-7.5K': '#FFB3B8',
    '$7.5K-10K': '#FF8088',
    '$10K-15K': '#FF4D58',
    '$15K-25K': '#ED1B2E',
    '$25K-50K': '#B31E29',
    '$50K-100K': '#8B1A1E',
    '>$100K': '#4A0E0E'
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    filters = request.args.to_dict()
    filtered_df = df.copy()
    
    if filters.get('state') and filters['state'] != 'all':
        filtered_df = filtered_df[filtered_df['State'] == filters['state']]
    
    if filters.get('city') and filters['city'] != 'all':
        filtered_df = filtered_df[filtered_df['City'] == filters['city']]
    
    if filters.get('gift_category') and filters['gift_category'] != 'all':
        filtered_df = filtered_df[filtered_df['Gift_Category'] == filters['gift_category']]
    
    min_gift = filters.get('min_gift')
    max_gift = filters.get('max_gift')
    if min_gift:
        try:
            min_gift = float(min_gift)
            filtered_df = filtered_df[filtered_df[' Gift $ '] >= min_gift]
        except ValueError:
            pass
    if max_gift:
        try:
            max_gift = float(max_gift)
            filtered_df = filtered_df[filtered_df[' Gift $ '] <= max_gift]
        except ValueError:
            pass
    
    map_type = filters.get('map_type', 'cluster')
    
    if map_type == 'cluster':
        fig = create_cluster_map(filtered_df)
    elif map_type == 'heatmap':
        fig = create_heatmap(filtered_df)
    elif map_type == 'choropleth':
        fig = create_choropleth(filtered_df)
    else:
        fig = create_point_map(filtered_df)
    
    stats = {
        'total_donors': len(filtered_df),
        'total_gifts': f"${filtered_df[' Gift $ '].sum():,.2f}",
        'avg_gift': f"${filtered_df[' Gift $ '].mean():,.2f}",
        'median_gift': f"${filtered_df[' Gift $ '].median():,.2f}",
        'top_states': filtered_df.groupby('State')[' Gift $ '].sum().nlargest(5).to_dict(),
        'gift_distribution': filtered_df['Gift_Category'].value_counts().to_dict()
    }
    
    return jsonify({
        'map': json.loads(plotly.utils.PlotlyJSONEncoder().encode(fig)),
        'stats': stats,
        'filters': {
            'states': sorted(df['State'].dropna().unique().tolist()),
            'cities': sorted(filtered_df['City'].dropna().unique().tolist()),
            'gift_categories': ['$5K', '$5K-7.5K', '$7.5K-10K', '$10K-15K', '$15K-25K', '$25K-50K', '$50K-100K', '>$100K']
        }
    })

def create_cluster_map(filtered_df):
    fig = go.Figure()
    
    hover_text = []
    for idx, row in filtered_df.iterrows():
        text = f"<b>{row['City']}, {row['State']}</b><br>"
        text += f"Gift: ${row[' Gift $ ']:,.2f}<br>"
        text += f"Donor #: {row['Donor #']}<br>"
        if pd.notna(row['Street Address']):
            text += f"Address: {row['Street Address']}"
        hover_text.append(text)
    
    # Add clustered scatter layer
    fig.add_trace(go.Scattermapbox(
        lon=filtered_df['X'],
        lat=filtered_df['Y'],
        mode='markers',
        marker=dict(
            size=10,
            color=filtered_df[' Gift $ '],
            colorscale=[
                [0, '#FFE6E8'],
                [0.2, '#FFB3B8'],
                [0.4, '#FF8088'],
                [0.6, '#FF4D58'],
                [0.8, '#ED1B2E'],
                [1, '#8B1A1E']
            ],
            showscale=True,
            colorbar=dict(
                title="Gift Amount",
                titlefont=dict(color=RED_CROSS_COLORS['dark_red']),
                tickfont=dict(color=RED_CROSS_COLORS['gray']),
                tickprefix="$",
                tickformat=",.0f"
            ),
            opacity=0.8
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        cluster=dict(
            enabled=True,
            size=40,
            step=1,
            color=['#FFE6E8', '#FFB3B8', '#FF8088', '#FF4D58', '#ED1B2E', '#B31E29', '#8B1A1E'],
            opacity=0.8,
            maxzoom=10
        ),
        showlegend=False
    ))
    
    fig.update_layout(
        mapbox=dict(
            style='carto-positron',
            center=dict(
                lat=filtered_df['Y'].mean() if len(filtered_df) > 0 else 39.8283,
                lon=filtered_df['X'].mean() if len(filtered_df) > 0 else -98.5795
            ),
            zoom=3 if len(filtered_df) > 100 else 5
        ),
        height=700,
        margin={"r":0,"t":40,"l":0,"b":0},
        title={
            'text': 'American Red Cross Donor Map',
            'font': {'size': 24, 'color': RED_CROSS_COLORS['primary_red'], 'family': 'Arial, sans-serif'}
        },
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=RED_CROSS_COLORS['primary_red'],
            borderwidth=2
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial, sans-serif",
            bordercolor=RED_CROSS_COLORS['primary_red']
        )
    )
    
    return fig

def create_heatmap(filtered_df):
    fig = go.Figure(go.Densitymapbox(
        lat=filtered_df['Y'],
        lon=filtered_df['X'],
        z=filtered_df[' Gift $ '],
        radius=20,
        colorscale=[
            [0, RED_CROSS_COLORS['white']],
            [0.2, '#FFE6E8'],
            [0.4, '#FFB3B8'],
            [0.6, '#FF8088'],
            [0.8, RED_CROSS_COLORS['primary_red']],
            [1, RED_CROSS_COLORS['dark_red']]
        ],
        showscale=True,
        colorbar=dict(
            title="Gift Amount",
            titlefont=dict(color=RED_CROSS_COLORS['dark_red']),
            tickfont=dict(color=RED_CROSS_COLORS['gray']),
            tickprefix="$"
        )
    ))
    
    fig.update_layout(
        mapbox=dict(
            style='carto-positron',
            center=dict(
                lat=filtered_df['Y'].mean() if len(filtered_df) > 0 else 39.8283,
                lon=filtered_df['X'].mean() if len(filtered_df) > 0 else -98.5795
            ),
            zoom=3 if len(filtered_df) > 100 else 5
        ),
        height=700,
        margin={"r":0,"t":40,"l":0,"b":0},
        title={
            'text': 'American Red Cross Donor Heatmap',
            'font': {'size': 24, 'color': RED_CROSS_COLORS['primary_red'], 'family': 'Arial, sans-serif'}
        }
    )
    
    return fig

def create_choropleth(filtered_df):
    state_data = filtered_df.groupby('State').agg({
        ' Gift $ ': 'sum',
        'Donor #': 'count'
    }).reset_index()
    state_data.columns = ['State', 'Total_Gifts', 'Donor_Count']
    
    fig = go.Figure(data=go.Choropleth(
        locations=state_data['State'],
        z=state_data['Total_Gifts'],
        locationmode='USA-states',
        colorscale=[
            [0, RED_CROSS_COLORS['white']],
            [0.2, '#FFE6E8'],
            [0.4, '#FFB3B8'],
            [0.6, '#FF8088'],
            [0.8, RED_CROSS_COLORS['primary_red']],
            [1, RED_CROSS_COLORS['dark_red']]
        ],
        text=state_data.apply(lambda x: f"{x['State']}<br>Donors: {x['Donor_Count']:,}<br>Total: ${x['Total_Gifts']:,.0f}", axis=1),
        hovertemplate='%{text}<extra></extra>',
        colorbar=dict(
            title="Total Donations",
            titlefont=dict(color=RED_CROSS_COLORS['dark_red']),
            tickfont=dict(color=RED_CROSS_COLORS['gray']),
            tickprefix="$"
        )
    ))
    
    fig.update_layout(
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'),
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
        ),
        height=700,
        margin={"r":0,"t":60,"l":0,"b":0},
        title={
            'text': 'American Red Cross Donations by State',
            'font': {'size': 24, 'color': RED_CROSS_COLORS['primary_red'], 'family': 'Arial, sans-serif'}
        }
    )
    
    return fig

def create_point_map(filtered_df):
    fig = go.Figure()
    
    fig.add_trace(go.Scattermapbox(
        lon=filtered_df['X'],
        lat=filtered_df['Y'],
        mode='markers',
        marker=dict(
            size=6,
            color=RED_CROSS_COLORS['primary_red'],
            opacity=0.7
        ),
        text=filtered_df.apply(lambda x: f"{x['City']}, {x['State']}<br>${x[' Gift $ ']:,.2f}", axis=1),
        hovertemplate='%{text}<extra></extra>'
    ))
    
    fig.update_layout(
        mapbox=dict(
            style='carto-positron',
            center=dict(
                lat=filtered_df['Y'].mean() if len(filtered_df) > 0 else 39.8283,
                lon=filtered_df['X'].mean() if len(filtered_df) > 0 else -98.5795
            ),
            zoom=3 if len(filtered_df) > 100 else 5
        ),
        height=700,
        margin={"r":0,"t":40,"l":0,"b":0},
        title={
            'text': 'American Red Cross Donor Locations',
            'font': {'size': 24, 'color': RED_CROSS_COLORS['primary_red'], 'family': 'Arial, sans-serif'}
        }
    )
    
    return fig

if __name__ == '__main__':
    app.run(debug=True, port=8080)