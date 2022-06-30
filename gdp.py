import folium
import pandas
import geopandas

url = 'http://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)_per_capita'
tables1 = pandas.read_html(url, match='Country/Territory')
df1 = tables1[0]  # changes data from List to DataFrame

# makes it single index
df1.columns = ['Country', 'Region', 'Estimate_IMF', 'Year1', 'Estimate_UN', 'Year2', 'Estimate_WB', 'Year3']
# makes it two columns only (Country, Estimate_UN)
df1 = df1.drop(columns=['Region', 'Year1', 'Year2', 'Year3', 'Estimate_IMF', 'Estimate_WB'])

df1['Country'] = df1['Country'].map(lambda x: x.rstrip('*'))
df1['Country'] = df1['Country'].map(lambda x: x.strip())
df1['Country'] = df1['Country'].str.replace('United States', 'United States of America')
df1['Country'] = df1['Country'].str.replace('DR Congo', 'Dem. Rep. Congo')
df1['Country'] = df1['Country'].str.replace('Central African Republic', 'Central African Rep.')
df1['Country'] = df1['Country'].str.replace('South Sudan', 'S. Sudan')
df1['Country'] = df1['Country'].str.replace('Czech Republic', 'Czechia')
df1['Country'] = df1['Country'].str.replace('Bosnia and Herzegovina', 'Bosnia and Herz.')
df1['Country'] = df1['Country'].str.replace('Ivory Coast', """Côte d'Ivoire""")
df1['Country'] = df1['Country'].str.replace('Dominican Republic', 'Dominican Rep.')
df1['Country'] = df1['Country'].str.replace('Eswatini', 'eSwatini')
df1['Country'] = df1['Country'].str.replace('Equatorial Guinea', 'Eq. Guinea')
df1.drop(df1[df1['Estimate_UN'] == '—'].index, inplace = True)
df1['Estimate_UN'] = df1['Estimate_UN'].apply(lambda g:int(str(g)))

### --- Change 'GDP Per Capita' values in GeoJsonToolTip from format of 12345.0 (USD) to €11,604 --- ###

df2 = df1.copy()

df2['Estimate_UN'] = df2['Estimate_UN'].apply(lambda g:g*0.94) # Convert USD to EUR

df3 = df2.copy()

df2['Estimate_UN'] = df2['Estimate_UN'].apply(lambda g:str(int(g)))
df2['Estimate_UN'] = '€' + df2['Estimate_UN'].astype(str)

length = (df2['Estimate_UN'].str.len())

df2.loc[length == 7, 'Estimate_UN'] = df2[['Estimate_UN']].astype(str).replace(r"(\d{3})(\d+)", r"\1,\2", regex=True)
df2.loc[length == 6, 'Estimate_UN'] = df2[['Estimate_UN']].astype(str).replace(r"(\d{2})(\d+)", r"\1,\2", regex=True)
df2.loc[length == 5, 'Estimate_UN'] = df2[['Estimate_UN']].astype(str).replace(r"(\d{1})(\d+)", r"\1,\2", regex=True)

### --- Create map --- ###

world = geopandas.read_file(geopandas.datasets.get_path('naturalearth_lowres'))
df1 = world.merge(df1, how='left', left_on=['name'], right_on=['Country'])
df1 = df1.dropna(subset=['Estimate_UN'])

df2 = world.merge(df2, how='left', left_on=['name'], right_on=['Country'])
df2 = df2.dropna(subset=['Estimate_UN'])

df3 = world.merge(df3, how='left', left_on=['name'], right_on=['Country'])
df3 = df3.dropna(subset=['Estimate_UN'])

my_map = folium.Map(location=(39.22753573470106, -3.650093262568073),
    zoom_start=2, 
    tiles = 'https://server.arcgisonline.com/arcgis/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', 
    attr = 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye,Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
    min_zoom=2, 
    min_lot=-179, 
    max_lot=179, 
    min_lat=-65, 
    max_lat=179, 
    max_bounds=True)

### --- Add tooltip --- ###

gdp = folium.FeatureGroup(name="GDP")

gdp.add_child(folium.GeoJson(data=df2, tooltip = folium.features.GeoJsonTooltip(
    fields=['Country','Estimate_UN'], 
    aliases=['Country:','GDP Per Capita:'],
    style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"),
    localize = True),
    style_function= lambda y:{
    'stroke':'false',
    'opacity':'0',
    }))

### --- Color countries --- ###

bins = list(df3["Estimate_UN"].quantile([0, 0.65, 0.78, 0.865, 0.94, 0.987, 1]))

folium.Choropleth(
    geo_data=df1,
    name="choropleth",
    data=df3,
    columns=["Country", "Estimate_UN"],
    key_on="feature.properties.name",
    fill_color="YlGnBu",
    fill_opacity=0.8,
    line_opacity=0.5,
    legend_name="GDP Per Capita (in EUR)",
    bins=bins,
    reset=True,
    ).add_to(my_map)

my_map.add_child(gdp)
my_map.save('index.html')
