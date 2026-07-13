import pytest
from movie_generator import get_mood_music

def test_get_mood_music_documentary():
    assert get_mood_music("Documentary style") == "cinematic.mp3"
    assert get_mood_music("cinematic documentary") == "cinematic.mp3"

def test_get_mood_music_educational():
    assert get_mood_music("Educational") == "ambient.mp3"
    assert get_mood_music("daily news") == "ambient.mp3"

def test_get_mood_music_motivational():
    assert get_mood_music("Motivational video") == "dramatic.mp3"
    assert get_mood_music("short clip") == "dramatic.mp3"

def test_get_mood_music_default():
    assert get_mood_music("unknown style") == "cinematic.mp3"
    assert get_mood_music("") == "cinematic.mp3"
