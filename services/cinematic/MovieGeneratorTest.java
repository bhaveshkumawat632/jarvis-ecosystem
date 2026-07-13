import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

// Note: This is a Java/JUnit representation of the tests for the get_mood_music function.
// Since the project is in Python, this is provided as a structural example.

public class MovieGeneratorTest {

    // Dummy method representing the Python function
    public String getMoodMusic(String style) {
        String styleLower = style.toLowerCase();
        if (styleLower.contains("documentary")) {
            return "cinematic.mp3";
        } else if (styleLower.contains("educational") || styleLower.contains("news")) {
            return "ambient.mp3";
        } else if (styleLower.contains("motivational") || styleLower.contains("short")) {
            return "dramatic.mp3";
        } else {
            return "cinematic.mp3";
        }
    }

    @Test
    public void testGetMoodMusicDocumentary() {
        assertEquals("cinematic.mp3", getMoodMusic("Documentary style"));
        assertEquals("cinematic.mp3", getMoodMusic("cinematic documentary"));
    }

    @Test
    public void testGetMoodMusicEducational() {
        assertEquals("ambient.mp3", getMoodMusic("Educational"));
        assertEquals("ambient.mp3", getMoodMusic("daily news"));
    }

    @Test
    public void testGetMoodMusicMotivational() {
        assertEquals("dramatic.mp3", getMoodMusic("Motivational video"));
        assertEquals("dramatic.mp3", getMoodMusic("short clip"));
    }

    @Test
    public void testGetMoodMusicDefault() {
        assertEquals("cinematic.mp3", getMoodMusic("unknown style"));
        assertEquals("cinematic.mp3", getMoodMusic(""));
    }
}
