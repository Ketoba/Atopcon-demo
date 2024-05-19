import dash
from dash import html, dcc, Input, Output, State
import folium



## Import helper functions
from helper import load_geojson, get_data_radius, plot_map, build_table, get_bar_charts, save_plots_to_pdf_bytes

# URLs of shapefiles on GitHub
building_footprints_url = 'https://raw.githubusercontent.com/DonToba/Atopcon/main/Building_Footprints_4326.geojson'
poi_url = 'https://raw.githubusercontent.com/DonToba/Atopcon/main/POIs.geojson'
roads_url = 'https://raw.githubusercontent.com/DonToba/Atopcon/main/roads.geojson'

# Default coordinates
default_latitude = 6.580364
default_longitude = 3.362485

## Download POIs, roads and bld footprints
building_footprints = load_geojson(building_footprints_url)
POIs = load_geojson(poi_url)
roads = load_geojson(roads_url)

universal_plots = []


# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

# Define layout and style
app.layout = html.Div(style={'backgroundColor': '#000', 'color': '#fff', 'fontFamily': 'Arial, sans-serif'}, children=[
    html.H1("ATOPCON DEMO BY NERVS", style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div([
        html.Label("Latitude", style={'fontWeight': 'bold'}),
        dcc.Input(id='input-lat', type='number', value=default_latitude, style={'marginRight': '20px'}),
        html.Label("Longitude", style={'fontWeight': 'bold'}),
        dcc.Input(id='input-lon', type='number', value=default_longitude, style={'marginRight': '20px'}),
        html.Button('Submit', id='submit-val', n_clicks=0, style={'marginTop': '20px', 'marginRight': '10px', 'backgroundColor': '#007bff', 'color': '#fff', 'border': 'none'}),
        html.Button('Generate Report', id='generate-report', n_clicks=0, style={'marginTop': '20px', 'marginRight': '10px', 'backgroundColor': '#007bff', 'color': '#fff', 'border': 'none'}),
        html.Button('Download Report', id='download-report', n_clicks=0, style={'marginTop': '20px', 'backgroundColor': '#007bff', 'color': '#fff', 'border': 'none'}),
        dcc.Download(id="download-report-link")
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div(id='map-container', style={'textAlign': 'center'}),
    html.Div(id='analysis-container', style={'textAlign': 'center', 'marginTop': '20px'}),   
    html.Div(id='download-report-output')
])

### Callback for the submit button
@app.callback(
    Output('map-container', 'children'),
    [Input('submit-val', 'n_clicks')],
    [State('input-lat', 'value'), State('input-lon', 'value')]
)
def update_map(n_clicks, latitude, longitude):
    # Initialize map with default location
    mymap = folium.Map(location=[default_latitude, default_longitude], zoom_start=15)
    
    # Check if submit button was clicked
    if n_clicks > 0:
        # Validate latitude and longitude
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            return html.Iframe(id='map-iframe', width='100%', height='600'), "Invalid latitude or longitude!"

        # Create marker for inputted location
        folium.Marker(location=[latitude, longitude], popup="Subject Site").add_to(mymap)

        # Create circle with 250m radius
        folium.Circle(location=[latitude, longitude], radius=250, color='blue', fill=True, fill_opacity=0.2).add_to(mymap)

        # Update map zoom to focus on circle and point
        mymap.fit_bounds([[latitude - 0.01, longitude - 0.01], [latitude + 0.01, longitude + 0.01]])

    # Save Folium map to HTML file
    map_html = "mymap.html"
    mymap.save(map_html)
    return html.Iframe(id='map-iframe', srcDoc=open(map_html).read(), width='100%', height='600')


### Call back to generate report
@app.callback(
    Output('analysis-container', 'children'),
    [Input('generate-report', 'n_clicks')],
    [State('input-lat', 'value'), State('input-lon', 'value')]
)
def generate_report_callback(n_clicks, latitude, longitude):
    # Check if the generate report button was clicked
    if n_clicks > 0:
        # Validate latitude and longitude
        if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
            return "Invalid latitude or longitude!"

        # Function to get data within the specified radius
        data = get_data_radius(latitude, longitude, building_footprints, roads, POIs)
        
        # You can then process the data further as needed for your report
        # For demonstration, let's just return the count of each type of data
        building_data = data[0]
        road_data = data[1]
        poi_data = data[2]
                # List to hold the chart image components
        chart_images = []
        # Get the map
        map_layout = plot_map(building_data)
        chart_images.append(map_layout[0])
        universal_plots.append(map_layout[1])

        #Get the df table
        chart_images.append(build_table(poi_data))

        # GEt the bar charts
        bar_charts = [
        building_data["Use"].rename("Chart showing Use of Buildings within 250m radius"),
        building_data["Height"].rename("Chart showing Height of Buildings within 250m radius"),
        road_data["Class"].rename("Chart showing road classes within 250m radius"),
        road_data["Condition"].rename("Chart showing condition of roads within 250m radius")
    ]
        for each in bar_charts:
            eachbarchart = get_bar_charts(each)
            chart_images.append(eachbarchart[0])
            universal_plots.append(eachbarchart[1])
        
        ### Add dataframe columns to universal_plots t process in the pdf
        pois_df = poi_data[['Name', 'Type']].copy()
        universal_plots.append(pois_df)

        # Arrange the images in a grid
        return html.Div([
            html.Div(chart_images[:2], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '2px'}),
            html.Div(chart_images[2:4], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '2px'}),
            html.Div(chart_images[4:], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '2px'})
        ])
        

    # If the button hasn't been clicked, return an empty div
    return html.Div()

### Callback to download the pdf
@app.callback(
    Output("download-report-link", "data"),
    [Input("download-report", "n_clicks")], prevent_initial_call=True)
def download(n_clicks):
    # Check if the button is clicked
    # Check if the button is clicked
    if n_clicks:
        pdf_bytes = save_plots_to_pdf_bytes(universal_plots)
    return dcc.send_bytes(pdf_bytes, "report.pdf")

if __name__ == '__main__':
    app.run_server(debug=True)
