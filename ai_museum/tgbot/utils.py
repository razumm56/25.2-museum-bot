from ai_museum.scripts.route.generation_route import route_builder

exhibits = {
    1: 'https://fotohosting.pro/i/exhibit1.hpzyl',
    2: 'https://fotohosting.pro/i/exhibit2.hpqDj',
    3: 'https://fotohosting.pro/i/exhibit3.hpzgu',
    4: 'https://fotohosting.pro/i/exhibit4.hpzny',
    5: 'https://fotohosting.pro/i/exhibit5.hpzsz'
}

def generate_map(exhibits) -> str:
    return route_builder.generate_route(exhibits)
