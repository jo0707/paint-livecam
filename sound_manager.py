import pygame
import os

# Initialize pygame mixer once
pygame.mixer.init()

# Sound file paths
SFX_DIR = "sfx"
BACKSOUND_FILE = os.path.join(SFX_DIR, "backsound.mp3")
CLICK_FILE = os.path.join(SFX_DIR, "click.mp3")
WRITING_FILE = os.path.join(SFX_DIR, "writing.mp3")

# Load sounds once
sounds = {
    'click': pygame.mixer.Sound(CLICK_FILE),
    'writing': pygame.mixer.Sound(WRITING_FILE),
}

bg_music_playing = False
def play_background():
    """Toggle background music on/off."""
    global bg_music_playing
    if bg_music_playing:
        pygame.mixer.music.stop()
        bg_music_playing = False
        print("Background music stopped")
    else:
        pygame.mixer.music.load(BACKSOUND_FILE)
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.5)
        bg_music_playing = True
        print("Background music started")

def play_click():
    """Play button click sound effect."""
    try:
        if 'click' in sounds:
            sounds['click'].set_volume(0.5)
            sounds['click'].play()
    except pygame.error as e:
        print(f"Error playing click sound: {e}")

writingChannel = None
def play_writing():
    """Play writing sound effect."""
    global writingChannel
    
    if not writingChannel:
        sounds['writing'].set_volume(0.5)
        writingChannel = sounds['writing'].play()
        return
    
    if writingChannel and not writingChannel.get_busy():
        sounds['writing'].set_volume(0.5)
        writingChannel = sounds['writing'].play()
        return