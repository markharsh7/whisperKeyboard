#ifndef WHISPER_JNI_H
#define WHISPER_JNI_H

#include <jni.h>

#ifdef __cplusplus
extern "C" {
#endif

JNIEXPORT jlong JNICALL
Java_com_whisperkeyboard_WhisperEngine_nativeInit(JNIEnv *env, jobject thiz,
    jstring modelPath, jboolean useGpu);

JNIEXPORT jstring JNICALL
Java_com_whisperkeyboard_WhisperEngine_nativeTranscribe(JNIEnv *env, jobject thiz,
    jlong contextPtr, jstring audioPath, jstring language, jint nThreads);

JNIEXPORT void JNICALL
Java_com_whisperkeyboard_WhisperEngine_nativeDestroy(JNIEnv *env, jobject thiz,
    jlong contextPtr);

#ifdef __cplusplus
}
#endif

#endif // WHISPER_JNI_H
