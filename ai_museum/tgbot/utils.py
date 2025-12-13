from ai_museum.scripts.route.generation_route import route_builder
from ai_museum.db.create_tabels import get_random_exhibits

exhibits = {
    1: 'https://fotohosting.pro/i/exhibit1.hpzyl',
    2: 'https://fotohosting.pro/i/exhibit2.hpqDj',
    3: 'https://fotohosting.pro/i/exhibit3.hpzgu',
    4: 'https://fotohosting.pro/i/exhibit4.hpzny',
    5: 'https://fotohosting.pro/i/exhibit5.hpzsz'
}

def generate_map(count: int) -> str:
    exhibits = get_random_exhibits(count)
    print(exhibits)
    return route_builder.generate_route(exhibits)