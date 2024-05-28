import joblib
import numpy as np
import pandas as pd
import librosa.feature
import librosa.util
import librosa.effects
import warnings


class Predictor:
    def __init__(self, model_path: str, buffer_length: float, chunk_length: float, sample_rate: int, chunk_cnt: int,
                 pred_threshold: float):
        buffer_size = int(buffer_length * sample_rate)
        chunk_size = int(chunk_length * sample_rate)
        if buffer_size <= 0 or chunk_size <= 0 or chunk_cnt <= 0 or sample_rate <= 0:
            raise ValueError("All size and count parameters must be positive integers")
        if pred_threshold <= 0 or pred_threshold >= 1:
            raise ValueError("Threshold must be between 0 and 1")
        if chunk_size * chunk_cnt < buffer_size:
            raise ValueError('Sum of sizes of all chunks must be at least the buffer size.')
        self._model = joblib.load(model_path)
        self._pred_threshold = pred_threshold
        self._chunk_size = chunk_size
        self._max_chunk_cnt = chunk_cnt
        self._sample_rate = sample_rate
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

    def _vectorize(self, clean_buffer: np.array) -> pd.DataFrame:
        chunk_count = self._max_chunk_cnt if self._chunk_size * self._max_chunk_cnt >= len(clean_buffer)\
            else int(np.ceil(len(clean_buffer) / self._chunk_size))
        hop_length = (len(clean_buffer) - self._chunk_size) // (chunk_count - 1) if self._max_chunk_cnt > 1 else 0
        chunks = librosa.util.frame(clean_buffer, frame_length=self._chunk_size, hop_length=hop_length, axis=0)
        predictors_rows = []
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", module="librosa")
            for chunk in chunks:
                chroma_stft = np.mean(np.ravel(librosa.feature.chroma_stft(
                    S=np.abs(librosa.stft(chunk)), sr=self._sample_rate)))
                rms = np.mean(np.squeeze(librosa.feature.rms(y=chunk)))
                spectral_centroid = np.mean(np.squeeze(librosa.feature.spectral_centroid(y=chunk, sr=self._sample_rate)))
                spectral_bandwidth = np.mean(np.squeeze(librosa.feature.spectral_bandwidth(y=chunk, sr=self._sample_rate)))
                spectral_rolloff = np.mean(np.squeeze(librosa.feature.spectral_rolloff(y=chunk, sr=self._sample_rate)))
                zero_crossing_rate = np.mean(np.squeeze(librosa.feature.zero_crossing_rate(y=chunk)))
                mfcc_features = np.mean(librosa.feature.mfcc(y=chunk, sr=self._sample_rate, n_mfcc=20).T, axis=0)
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
        """
        intervals = librosa.effects.split(y=buffer, top_db=20)
        clean_buffer = np.concatenate([buffer[start:end] for start, end in intervals])

        print(f"Buffer: {len(buffer)}, clean buffer: {len(clean_buffer)}")
        clean_buffer = buffer
        if len(clean_buffer) < 0.5 * len(buffer):
            return False"""
        clean_buffer = buffer
        predictors_df = self._vectorize(buffer)
        predictions = self._model.predict(predictors_df)
        return True if np.count_nonzero(predictions) < self._pred_threshold * len(predictions) else False

    def fake_ratio(self, buffer: np.array):
        predictors_df = self._vectorize(buffer)
        predictions = self._model.predict(predictors_df)
        return np.divide(len(predictions) - np.count_nonzero(predictions), len(predictions))
