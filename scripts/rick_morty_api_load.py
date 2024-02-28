import requests
import pandas as pd
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, JSON, ARRAY, ForeignKey
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Load environment variables
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST') 
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')
db_schema = os.getenv('DB_SCHEMA')

# Initialize the database engine
connection_string = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
engine = create_engine(connection_string)

def create_schema_if_not_exists(engine, db_schema):
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {db_schema};"))
        conn.execute("COMMIT;")  

# create schema and table
def define_schema_and_tables():
    metadata = MetaData(schema=db_schema)

    # Define tables
    characters = Table('characters', metadata,
                       Column('id', Integer, primary_key=True),
                       Column('name', String),
                       Column('status', String),
                       Column('species', String),
                       Column('type', String),
                       Column('gender', String),
                       Column('origin', JSON),
                       Column('location', JSON),
                       Column('image', String),
                       Column('episode', ARRAY(String)),
                       Column('url', String),
                       Column('created', String),
                       Column('location_id', Integer, ForeignKey(f'{db_schema}.locations.id')))
    
    locations = Table('locations', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('name', String),
                      Column('type', String),
                      Column('dimension', String),
                      Column('residents', ARRAY(String)),
                      Column('url', String),
                      Column('created', String))
    
    # Create schema if not exists and tables
    create_schema_if_not_exists(engine, db_schema)
    with engine.begin() as conn: 
        metadata.create_all(conn)

# function to fetch from API
def fetch_data_from_api(endpoint):
    results = []
    url = endpoint
    while url:
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f'API request failed with status code {response.status_code}')
        data = response.json()
        results.extend(data['results'])
        url = data['info']['next']
    return results

# function to fetch characters data from API
def fetch_characters():
    api_endpoint = 'https://rickandmortyapi.com/api'
    characters_data = fetch_data_from_api(f'{api_endpoint}/character')
    characters_df = pd.DataFrame(characters_data)
    characters_df['origin'] = characters_df['origin'].apply(lambda x: json.dumps(x))
    characters_df['location'] = characters_df['location'].apply(lambda x: json.dumps(x))
    characters_df['episode'] = characters_df['episode'].apply(lambda x: json.dumps(x))
    characters_df['location_id'] = characters_df['location'].apply(lambda x: int(json.loads(x)['url'].split('/')[-1]) if json.loads(x)['url'] else None)
    return characters_df

# function to fetch locations data from API
def fetch_locations():
    api_endpoint = 'https://rickandmortyapi.com/api'
    locations_data = fetch_data_from_api(f'{api_endpoint}/location')
    locations_df = pd.DataFrame(locations_data)
    locations_df['residents'] = locations_df['residents'].apply(lambda x: json.dumps(x))
    return locations_df

# functions to insert character data
def insert_character_data():
    characters_df = fetch_characters()
    table_name = 'characters'
    with engine.begin() as conn: 
        characters_df.to_sql(table_name, con=conn, schema=db_schema, if_exists='replace', index=False, method='multi')
        print('Inserted to character table successfully!')

# function to insert location data
def insert_location_data():
    locations_df = fetch_locations()
    table_name = 'locations'
    with engine.begin() as conn:  
        locations_df.to_sql(table_name, con=conn, schema=db_schema, if_exists='replace', index=False, method='multi')
        print('Inserted to location table successfully!')
