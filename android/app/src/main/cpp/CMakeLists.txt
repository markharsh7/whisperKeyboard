cmake_minimum_required(VERSION 3.22.1)
project("whisperkeyboard_jni")

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(WHISPER_DIR ${CMAKE_CURRENT_SOURCE_DIR}/whisper.cpp)

include(FetchContent)
FetchContent_Declare(ggml SOURCE_DIR ${WHISPER_DIR}/ggml)
FetchContent_MakeAvailable(ggml)

set(WHISPER_VERSION "1.8.4")

add_library(whisper_jni SHARED
    ${WHISPER_DIR}/src/whisper.cpp
    whisper_jni.cpp
)

target_include_directories(whisper_jni PRIVATE
    ${WHISPER_DIR}
    ${WHISPER_DIR}/src
    ${WHISPER_DIR}/include
    ${WHISPER_DIR}/ggml/include
    ${WHISPER_DIR}/ggml/src
    ${WHISPER_DIR}/ggml/src/ggml-cpu
)

find_library(LOG_LIB log)

target_link_libraries(whisper_jni
    ggml
    ${LOG_LIB}
    android
)

target_compile_definitions(whisper_jni PUBLIC GGML_USE_CPU)
target_compile_definitions(whisper_jni PRIVATE WHISPER_VERSION="${WHISPER_VERSION}")

if (NOT ${CMAKE_BUILD_TYPE} STREQUAL "Debug")
    target_compile_options(whisper_jni PRIVATE -O3)
    target_compile_options(whisper_jni PRIVATE -fvisibility=hidden -fvisibility-inlines-hidden)
    target_compile_options(whisper_jni PRIVATE -ffunction-sections -fdata-sections)
endif()
