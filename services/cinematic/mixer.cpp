#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <string>
#include <algorithm>
#include <cstdint>

struct WAVFormat {
    uint16_t numChannels = 2;
    uint32_t sampleRate = 44100;
    uint16_t bitsPerSample = 16;
};

#pragma pack(push, 1)
struct WAVHeader {
    char chunkID[4] = {'R', 'I', 'F', 'F'};
    uint32_t chunkSize;
    char format[4] = {'W', 'A', 'V', 'E'};
    char subchunk1ID[4] = {'f', 'm', 't', ' '};
    uint32_t subchunk1Size = 16;
    uint16_t audioFormat = 1;
    uint16_t numChannels;
    uint32_t sampleRate;
    uint32_t byteRate;
    uint16_t blockAlign;
    uint16_t bitsPerSample = 16;
    char subchunk2ID[4] = {'d', 'a', 't', 'a'};
    uint32_t subchunk2Size;
};
#pragma pack(pop)

bool readWavFile(const std::string& filename, WAVFormat& format, std::vector<int16_t>& data) {
    std::ifstream file(filename, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Warning: Cannot open file " << filename << " (Will treat as silence)" << std::endl;
        return false;
    }
    char chunkID[4];
    uint32_t chunkSize;
    file.read(chunkID, 4);
    file.read(reinterpret_cast<char*>(&chunkSize), 4);
    char formatName[4];
    file.read(formatName, 4);
    
    if (file.gcount() < 4 || std::string(chunkID, 4) != "RIFF" || std::string(formatName, 4) != "WAVE") return false;
    bool fmtFound = false, dataFound = false;
    while (file.peek() != EOF) {
        char subChunkID[4];
        uint32_t subChunkSize;
        file.read(subChunkID, 4);
        if (file.gcount() < 4) break;
        file.read(reinterpret_cast<char*>(&subChunkSize), 4);
        if (file.gcount() < 4) break;
        std::string sid(subChunkID, 4);
        if (sid == "fmt ") {
            uint16_t audioFormat = 0;
            file.read(reinterpret_cast<char*>(&audioFormat), 2);
            file.read(reinterpret_cast<char*>(&format.numChannels), 2);
            file.read(reinterpret_cast<char*>(&format.sampleRate), 4);
            file.seekg(6, std::ios::cur);
            file.read(reinterpret_cast<char*>(&format.bitsPerSample), 2);
            if (subChunkSize > 16) file.seekg(subChunkSize - 16, std::ios::cur);
            fmtFound = true;
        } else if (sid == "data") {
            size_t sampleCount = subChunkSize / sizeof(int16_t);
            data.resize(sampleCount);
            file.read(reinterpret_cast<char*>(data.data()), subChunkSize);
            dataFound = true;
            break;
        } else file.seekg(subChunkSize, std::ios::cur);
    }
    return fmtFound && dataFound;
}

bool writeWavFile(const std::string& filename, const WAVHeader& header, const std::vector<int16_t>& data) {
    std::ofstream file(filename, std::ios::binary);
    if (!file.is_open()) return false;
    file.write(reinterpret_cast<const char*>(&header), sizeof(WAVHeader));
    file.write(reinterpret_cast<const char*>(data.data()), data.size() * sizeof(int16_t));
    return true;
}

int main(int argc, char* argv[]) {
    if (argc < 5) {
        std::cout << "Usage: " << argv[0] << " <voice.wav> <ambience.wav> <music.wav> <output.wav>\n";
        return 1;
    }

    std::string voicePath = argv[1];
    std::string ambPath = argv[2];
    std::string musicPath = argv[3];
    std::string outputPath = argv[4];

    WAVFormat voiceFormat, ambFormat, musicFormat;
    std::vector<int16_t> voiceData, ambData, musicData;

    bool hasVoice = readWavFile(voicePath, voiceFormat, voiceData);
    bool hasAmb = readWavFile(ambPath, ambFormat, ambData);
    bool hasMusic = readWavFile(musicPath, musicFormat, musicData);

    size_t sampleRate = 44100;
    size_t channels = 2;
    
    // Fallbacks if formatting fails, use standard format
    if (hasVoice) { sampleRate = voiceFormat.sampleRate; channels = voiceFormat.numChannels; }
    else if (hasMusic) { sampleRate = musicFormat.sampleRate; channels = musicFormat.numChannels; }
    
    size_t voiceFrames = voiceData.size() / channels;
    size_t ambFrames = ambData.size() / channels;
    size_t musicFrames = musicData.size() / channels;
    
    size_t max_frames = std::max({voiceFrames, ambFrames, musicFrames});
    if (max_frames == 0) {
        std::cerr << "All inputs are empty!" << std::endl;
        return 1;
    }
    
    std::vector<int16_t> outputData(max_frames * channels, 0);

    const float MUSIC_DUCK_RATIO = 0.15f;    // Approx -16dB
    const float AMBIENCE_DUCK_RATIO = 0.50f; // Approx -6dB
    const float THRESHOLD = 0.05f * 32768.0f; // Voice activation threshold (amplitude)

    // Smooth transition tracking
    float current_music_gain = 1.0f;
    float current_amb_gain = 1.0f;
    float attack = 0.01f;
    float release = 0.001f;

    for (size_t i = 0; i < max_frames; ++i) {
        float voice_sample_l = (i < voiceFrames) ? voiceData[i * channels] : 0.0f;
        float amb_sample_l = (i < ambFrames) ? ambData[i * channels] : 0.0f;
        float music_sample_l = (i < musicFrames) ? musicData[i * channels] : 0.0f;

        float voice_sample_r = (channels > 1 && i < voiceFrames) ? voiceData[i * channels + 1] : voice_sample_l;
        float amb_sample_r = (channels > 1 && i < ambFrames) ? ambData[i * channels + 1] : amb_sample_l;
        float music_sample_r = (channels > 1 && i < musicFrames) ? musicData[i * channels + 1] : music_sample_l;
        
        float envelope = std::max(std::fabs(voice_sample_l), std::fabs(voice_sample_r)); 
        
        float target_music_gain = 1.0f;
        float target_amb_gain = 1.0f;
        
        if (envelope > THRESHOLD) {
            target_music_gain = MUSIC_DUCK_RATIO;
            target_amb_gain = AMBIENCE_DUCK_RATIO;
        }

        // Smoothing
        if (current_music_gain > target_music_gain) current_music_gain -= attack;
        else if (current_music_gain < target_music_gain) current_music_gain += release;
        
        if (current_amb_gain > target_amb_gain) current_amb_gain -= attack;
        else if (current_amb_gain < target_amb_gain) current_amb_gain += release;
        
        // Clamp gains
        current_music_gain = std::max(MUSIC_DUCK_RATIO, std::min(1.0f, current_music_gain));
        current_amb_gain = std::max(AMBIENCE_DUCK_RATIO, std::min(1.0f, current_amb_gain));

        // Flatten and limit the Master Mix
        float mixed_l = voice_sample_l + (amb_sample_l * current_amb_gain) + (music_sample_l * current_music_gain);
        float mixed_r = voice_sample_r + (amb_sample_r * current_amb_gain) + (music_sample_r * current_music_gain);
        
        if (mixed_l > 32767.0f) mixed_l = 32767.0f;
        if (mixed_l < -32768.0f) mixed_l = -32768.0f;
        if (mixed_r > 32767.0f) mixed_r = 32767.0f;
        if (mixed_r < -32768.0f) mixed_r = -32768.0f;
        
        outputData[i * channels] = static_cast<int16_t>(mixed_l);
        if (channels > 1) {
            outputData[i * channels + 1] = static_cast<int16_t>(mixed_r);
        }
    }
    
    WAVHeader outHeader;
    outHeader.numChannels = channels;
    outHeader.sampleRate = sampleRate;
    outHeader.bitsPerSample = 16;
    outHeader.blockAlign = channels * 2;
    outHeader.byteRate = sampleRate * outHeader.blockAlign;
    outHeader.subchunk2Size = outputData.size() * sizeof(int16_t);
    outHeader.chunkSize = 36 + outHeader.subchunk2Size;

    if (!writeWavFile(outputPath, outHeader, outputData)) return 1;
    return 0;
}
