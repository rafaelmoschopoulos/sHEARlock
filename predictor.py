import joblib
import numpy as np
import pandas as pd
import librosa.feature
import librosa.util


class Predictor:
    def __init__(self, model_path: str, buffer_size: int, chunk_size: int, sample_rate: int, chunk_cnt: int,
                 pred_threshold: float):
        if buffer_size <= 0 or chunk_size <= 0 or chunk_cnt <= 0 or sample_rate <= 0:
            raise ValueError("All size and count parameters must be positive integers")
        if pred_threshold <= 0 or pred_threshold >= 1:
            raise ValueError("Threshold must be between 0 and 1")
        if chunk_size * chunk_cnt < buffer_size:
            raise ValueError('Sum of sizes of all chunks must be at least the buffer size.')
        self.__model = joblib.load(model_path)
        self.__pred_threshold = pred_threshold
        self.__chunk_size = chunk_size
        self.__chunk_cnt = chunk_cnt
        self.__sample_rate = sample_rate
        self.__hop_length = (buffer_size - chunk_size) // (chunk_cnt - 1) if chunk_cnt > 1 else 0
        """
            |-------------------- BUFFER --------------------|
            |-- CHUNK 1 --|                                  .
            .      |-- CHUNK 2 --|                           .
            .      .      |-- CHUNK 3 --|                    .
            .      .      .             .     [ etc ]        .
            .      .      <-chunk size->                     .
            <-hop-><-hop->                                   .
            .<----------------- buffer size ---------------->.
        """

    def __vectorize(self, buffer: np.array) -> pd.DataFrame:
        chunks = librosa.util.frame(buffer, frame_length=self.__chunk_size, hop_length=self.__hop_length, axis=0)
        predictors_rows = []
        for chunk in chunks:
            chroma_stft = np.mean(np.ravel(librosa.feature.chroma_stft(
                S=np.abs(librosa.stft(chunk)), sr=self.__sample_rate)))
            rms = np.mean(np.squeeze(librosa.feature.rms(y=chunk)))
            spectral_centroid = np.mean(np.squeeze(librosa.feature.spectral_centroid(y=chunk, sr=self.__sample_rate)))
            spectral_bandwidth = np.mean(np.squeeze(librosa.feature.spectral_bandwidth(y=chunk, sr=self.__sample_rate)))
            spectral_rolloff = np.mean(np.squeeze(librosa.feature.spectral_rolloff(y=chunk, sr=self.__sample_rate)))
            zero_crossing_rate = np.mean(np.squeeze(librosa.feature.zero_crossing_rate(y=chunk)))
            mfcc_features = np.mean(librosa.feature.mfcc(y=chunk, sr=self.__sample_rate, n_mfcc=20).T, axis=0)
            features = {
                'chroma_stft': chroma_stft,
                'rms': rms,
                'spectral_centroid': spectral_centroid,
                'spectral_bandwidth': spectral_bandwidth,
                'rolloff': spectral_rolloff,
                'zero_crossing_rate': zero_crossing_rate
            }
            for i, mfcc in enumerate(mfcc_features):
                features[f'mfcc{i + 1}'] = mfcc
            predictors_rows.append(features)

        return pd.DataFrame(predictors_rows)

    def is_deepfake(self, buffer: np.ndarray):
        predictors_df = self.__vectorize(buffer)
        predictions = self.__model.predict(predictors_df)
        return True if np.count_nonzero(predictions) >= self.__pred_threshold * len(predictions) else False
