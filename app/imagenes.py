"""Fotos de referencia del catálogo, por (marca, modelo).

Se usan cuando el vehículo no tiene `imagen_url` en la base de datos (p. ej. bases creadas antes de
que existieran las fotos). Si la foto no carga, la tarjeta muestra la silueta del tipo de carrocería.
Para alojar las fotos en el propio proyecto, guárdalas en static/img/vehiculos/ y reemplaza la URL
por "/static/img/vehiculos/<archivo>.jpg".
"""

FOTOS = {
    ("Tesla", "Model 3 Long Range"): "https://hips.hearstapps.com/hmg-prod/images/2024-tesla-model-3-long-range-rwd-120-66feb66119c63.jpg?crop=0.571xw:0.479xh;0.146xw,0.416xh&resize=2048:*",
    ("Kia", "EV6"): "https://d2u1z1lopyfwlx.cloudfront.net/thumbnails/aa93bc08-60da-5b34-a454-a7c759571473/a1ae5bb0-9c73-5189-9e36-292bdc04a608.jpg",
    ("BMW", "i4"): "https://d2u1z1lopyfwlx.cloudfront.net/thumbnails/d6898721-147a-553e-a37c-e9f272c21a89/317e674c-7cf8-59cd-8e53-d9e5af1fe5ed.jpg",
    ("Chevrolet", "Bolt EV"): "https://lp-auto-assets.s3.amazonaws.com/23/chevrolet/bolt-ev/M3/header.jpg",
    ("Nissan", "Leaf"): "https://static0.carbuzzimages.com/wordpress/wp-content/uploads/gallery-images/original/402000/100/402104.jpg?q=50&fit=contain&w=750&h=422&dpr=1.5",
    ("Volvo", "XC40 Recharge"): "https://img.sm360.ca/ir/w1280h1024/images/article/beaucage/121995//article-essai-volvo-xc40-recharge-2024-photos_11699642294458.jpg",
    ("Toyota", "Corolla Hybrid"): "https://images.cars.com/cldstatic/wp-content/uploads/23-Toyota-Corolla-Hybrid-oem-scaled.jpg",
    ("Kia", "Niro Hybrid"): "https://images.cars.com/cldstatic/wp-content/uploads/kia-niro-hev-2023-32-exterior-front-angle-green-suv.jpg",
    ("Mazda", "CX-5"): "https://images.cars.com/cldstatic/wp-content/uploads/mazda-cx5-turbo-signature-2023-dynamic-front-oem.jpg",
    ("Renault", "Duster"): "https://img.autofun.co.id/file/e3ea34957d6140b0abcf4f66dbbcf31d.jpg",
}


def foto_de(marca, modelo):
    return FOTOS.get((marca, modelo))
