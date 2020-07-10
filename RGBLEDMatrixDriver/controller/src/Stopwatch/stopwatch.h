#ifndef STOPWATCH_H
#define STOPWATCH_H

#include <Arduino.h>


class Stopwatch
{
private:
    uint32_t m_iCurrentTimeMs;
    
public:
    Stopwatch()
        : m_iCurrentTimeMs(millis()) {}
    
    uint32_t timeit(bool reset=false)
    {
        // NOTE: In the following arithmetic, it is possible for
        //       'timeElasped' to be negative but it can only happen
        //       after 50 days. Realistically, no non-server computer
        //       is ON that long so we won't bother correcting.
        auto timeElasped = (millis() - this->m_iCurrentTimeMs);
        
        if (reset)
            this->m_iCurrentTimeMs = millis();
        
        return timeElasped;
    }
};
#endif