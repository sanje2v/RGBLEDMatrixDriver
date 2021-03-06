#include "decompressor.h"


Decompressor::Decompressor()
{
    this->reset();
}

void Decompressor::feed(uint8_t data,
                        uint8_t *pFramesBuffer,
                        uint16_t *pCurrentWriteBytePos_Red,
                        uint16_t *pCurrentWriteBytePos_Green,
                        uint16_t *pCurrentWriteBytePos_Blue,
                        uint16_t totalFramesBufferSize)
{
    // Write dataByte to current position in buffer
    this->m_buffer[this->m_nextBufferWriteIndex] = data;
    
    /* NOTE: Expected 3 bytes data to decompress will be in the following format:
        [XXXXX, YYY], [XXXXX, YYY], [XXXXX, YYY]
        [Red, Times], [Green, Times], [Blue, Times]
    */
    if ((this->m_nextBufferWriteIndex + 1) == BUFFER_SIZE)
    {
        // Buffer full, so decompress into frame buffer
        auto redByte = (this->m_buffer[0] & 0xF8);
        auto redTimes = (this->m_buffer[0] & 0x07);
        auto greenByte = (this->m_buffer[1] & 0xF8);
        auto greenTimes = (this->m_buffer[1] & 0x07);
        auto blueByte = (this->m_buffer[2] & 0xF8);
        auto blueTimes = (this->m_buffer[2] & 0x07);
        
        #ifdef DEBUG
        this->m_totalBytesDecompressed += (redTimes + greenTimes + blueTimes);
        #endif
        
        const uint8_t NUM_COLOR_CHANNELS = 3;
        uint8_t maxTimes = max(max(redTimes, greenTimes), blueTimes);
        for (uint8_t i = 0; i < maxTimes; ++i)
        {
            // For each channel, do repeats if we need to
            // NOTE: We have reordered writes to match WS2812's
            //       color byte order. This is predicated on the
            //       belief that this more sequential write would
            //       be less taxing on memory writes.
            auto ditherAmount = static_cast<int8_t>(random(-7, 8));
            if (greenTimes > 0)
            {
                --greenTimes;
                pFramesBuffer[*pCurrentWriteBytePos_Green] = Decompressor::addDithering(greenByte, ditherAmount);
                
                *pCurrentWriteBytePos_Green = (*pCurrentWriteBytePos_Green + NUM_COLOR_CHANNELS) % totalFramesBufferSize;
            }
            
            if (redTimes > 0)
            {
                --redTimes;
                pFramesBuffer[*pCurrentWriteBytePos_Red] = Decompressor::addDithering(redByte, ditherAmount);
                
                *pCurrentWriteBytePos_Red = (*pCurrentWriteBytePos_Red + NUM_COLOR_CHANNELS) % totalFramesBufferSize;
            }
            
            if (blueTimes > 0)
            {
                --blueTimes;
                pFramesBuffer[*pCurrentWriteBytePos_Blue] = Decompressor::addDithering(blueByte, ditherAmount);
                
                *pCurrentWriteBytePos_Blue = (*pCurrentWriteBytePos_Blue + NUM_COLOR_CHANNELS) % totalFramesBufferSize;
            }
        }
    }
    
    // Increment buffer write pos for next write
    this->m_nextBufferWriteIndex = (this->m_nextBufferWriteIndex + 1) % BUFFER_SIZE;
}

#ifdef DEBUG
uint16_t Decompressor::getTotalBytesDecompressed()
{
    return this->m_totalBytesDecompressed;
}

void Decompressor::resetTotalBytesDecompressed()
{
    this->m_totalBytesDecompressed = 0;
}
#endif

void Decompressor::reset()
{
    this->m_nextBufferWriteIndex = 0;
#ifdef DEBUG
    this->resetTotalBytesDecompressed();
#endif
}

uint8_t Decompressor::addDithering(uint8_t dataByte, int8_t amount)
{
    return (dataByte == 0x00 ? 
            dataByte :
            static_cast<uint8_t>(min(max(static_cast<int16_t>(dataByte) + amount, 0x00), 0xFF)));
}