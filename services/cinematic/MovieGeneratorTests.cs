using NUnit.Framework;

// Note: This is a C#/NUnit representation of the tests for the get_mood_music function.
// Since the project is in Python, this is provided as a structural example.

namespace JarvisUniversal.Tests
{
    [TestFixture]
    public class MovieGeneratorTests
    {
        // Dummy method representing the Python function
        public string GetMoodMusic(string style)
        {
            string styleLower = style.ToLower();
            if (styleLower.Contains("documentary"))
            {
                return "cinematic.mp3";
            }
            else if (styleLower.Contains("educational") || styleLower.Contains("news"))
            {
                return "ambient.mp3";
            }
            else if (styleLower.Contains("motivational") || styleLower.Contains("short"))
            {
                return "dramatic.mp3";
            }
            else
            {
                return "cinematic.mp3";
            }
        }

        [Test]
        public void TestGetMoodMusic_Documentary()
        {
            Assert.AreEqual("cinematic.mp3", GetMoodMusic("Documentary style"));
            Assert.AreEqual("cinematic.mp3", GetMoodMusic("cinematic documentary"));
        }

        [Test]
        public void TestGetMoodMusic_Educational()
        {
            Assert.AreEqual("ambient.mp3", GetMoodMusic("Educational"));
            Assert.AreEqual("ambient.mp3", GetMoodMusic("daily news"));
        }

        [Test]
        public void TestGetMoodMusic_Motivational()
        {
            Assert.AreEqual("dramatic.mp3", GetMoodMusic("Motivational video"));
            Assert.AreEqual("dramatic.mp3", GetMoodMusic("short clip"));
        }

        [Test]
        public void TestGetMoodMusic_Default()
        {
            Assert.AreEqual("cinematic.mp3", GetMoodMusic("unknown style"));
            Assert.AreEqual("cinematic.mp3", GetMoodMusic(""));
        }
    }
}
