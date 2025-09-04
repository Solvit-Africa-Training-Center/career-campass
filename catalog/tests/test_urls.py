from django.urls import reverse, resolve

def test_institution_list_url():
    url = reverse("institution-list")
    assert resolve(url).view_name == "institution-list"