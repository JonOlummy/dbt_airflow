WITH merged_data AS (
    SELECT
            c.id as character_id,
            c.name as character_name,
            c.status as character_status,
            c.species as character_species,
            c.type as character_type,
            c.gender as character_gender,
            c.image as character_image,
            c.episode as character_episode,
            c.url as character_url,
            c.created as character_created,
            l.id as location_id,
            l.name as location_name,
            l.type as location_type,
            l.dimension as location_dimension,
            l.url as location_url,
            l.created as location_created
    FROM {{ source('rick_and_morty', 'characters') }} c
    LEFT JOIN {{ source('rick_and_morty', 'locations') }} l ON c.location_id = l.id
)

SELECT * FROM merged_data