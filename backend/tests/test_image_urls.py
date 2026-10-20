from utils.image_urls import (
    gcs_public_url,
    image_object_name,
    proxy_image_url,
    public_image_url,
    public_image_urls,
    thumbnail_object_name,
    thumbnail_url,
)


def test_gcs_public_url():
    assert gcs_public_url('products/abc.jpeg') == (
        'https://storage.googleapis.com/gsf-app-catalog-images/products/abc.jpeg'
    )


def test_proxy_image_url():
    assert proxy_image_url('products/abc.jpeg') == (
        'https://backend.grainstoryfarm.ca/api/images/products/abc.jpeg'
    )


def test_catalog_urls_point_at_cloud_storage():
    assert public_image_url(
        'https://backend.grainstoryfarm.ca/api/images/products/abc.jpeg'
    ) == 'https://storage.googleapis.com/gsf-app-catalog-images/products/abc.jpeg'
    assert public_image_url(
        'https://storage.googleapis.com/gsf-app-catalog-images/recipes/abc.jpg'
    ) == 'https://storage.googleapis.com/gsf-app-catalog-images/recipes/abc.jpg'


def test_delivery_urls_stay_on_the_proxy():
    assert public_image_url(
        'https://storage.googleapis.com/gsf-app-catalog-images/deliveries/door.jpg'
    ) == 'https://backend.grainstoryfarm.ca/api/images/deliveries/door.jpg'
    assert thumbnail_url(
        'https://backend.grainstoryfarm.ca/api/images/deliveries/door.jpg'
    ) is None


def test_strips_signed_query_string():
    signed = (
        'https://storage.googleapis.com/gsf-app-catalog-images/products/abc.jpeg'
        '?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Signature=deadbeef'
    )
    assert public_image_url(signed) == (
        'https://storage.googleapis.com/gsf-app-catalog-images/products/abc.jpeg'
    )


def test_rewrites_relative_and_localhost():
    assert public_image_url('/api/images/products/abc.png') == (
        'https://storage.googleapis.com/gsf-app-catalog-images/products/abc.png'
    )
    assert public_image_url(
        'http://localhost:5000/api/images/products/abc.png'
    ) == 'https://storage.googleapis.com/gsf-app-catalog-images/products/abc.png'


def test_leaves_other_urls_alone():
    assert public_image_url('https://example.com/pic.jpg') == 'https://example.com/pic.jpg'
    assert public_image_url(None) is None


def test_image_object_name():
    assert image_object_name(
        'https://backend.grainstoryfarm.ca/api/images/products/abc.jpeg'
    ) == 'products/abc.jpeg'
    assert image_object_name(
        'https://storage.googleapis.com/gsf-app-catalog-images/products/abc.jpeg?X-Goog-Signature=x'
    ) == 'products/abc.jpeg'


def test_thumbnail_object_name():
    assert thumbnail_object_name('products/abc.png') == 'products/thumbs/abc.jpg'
    assert thumbnail_object_name('recipes/abc.jpg') == 'recipes/thumbs/abc.jpg'
    assert thumbnail_object_name('products/thumbs/abc.jpg') == 'products/thumbs/abc.jpg'
    assert thumbnail_object_name('deliveries/door.jpg') is None


def test_thumbnail_url():
    assert thumbnail_url(
        'https://backend.grainstoryfarm.ca/api/images/products/abc.jpeg'
    ) == 'https://storage.googleapis.com/gsf-app-catalog-images/products/thumbs/abc.jpg'


def test_public_image_urls():
    assert public_image_urls([
        'https://backend.grainstoryfarm.ca/api/images/products/a.jpeg',
        'https://storage.googleapis.com/gsf-app-catalog-images/products/b.jpeg',
    ]) == [
        'https://storage.googleapis.com/gsf-app-catalog-images/products/a.jpeg',
        'https://storage.googleapis.com/gsf-app-catalog-images/products/b.jpeg',
    ]
