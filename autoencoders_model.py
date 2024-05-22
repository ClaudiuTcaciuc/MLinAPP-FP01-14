import os
import tensorflow as tf
import keras_tuner as kt
import matplotlib.pyplot as plt

class Autoencoder:
    def __init__(self, input_shape, max_epochs=50, output_dir='./models_output'):
        self.input_shape = input_shape
        self.output_dir = output_dir
        self.max_epochs = max_epochs
        self.tuner = None
        self.model = None
        
        print(f"Autoencoder classifier n2")
        
        try:
            os.makedirs(output_dir)
        except FileExistsError:
            print(f"Directory {output_dir} already exists.")
    
    def build_model(self, hp):
        model = tf.keras.Sequential()
        model.add(tf.keras.layers.InputLayer(input_shape=self.input_shape))
        
        # Encoder
        for i in range(hp.Int('num_layers', 1, 3)):
            model.add(tf.keras.layers.Dense(
                units=hp.Int('units_' + str(i), 32, 256, 32),
                activation='relu'
            ))
        
        # Bottleneck layer (latent space representation)
        model.add(tf.keras.layers.Dense(hp.Int('latent_dim', 16, 64, 16), activation='relu'))
        
        # Decoder
        for i in reversed(range(hp.Int('num_layers', 1, 3))):
            model.add(tf.keras.layers.Dense(
                units=hp.Int('units_' + str(i), 32, 256, 32),
                activation='relu'
            ))
        
        model.add(tf.keras.layers.Dense(self.input_shape[0], activation='sigmoid'))
        model.compile(optimizer=tf.keras.optimizers.Adam(
            hp.Choice('learning_rate', values=[1e-2, 1e-3, 1e-4])),
            loss='mse'
        )
        model.summary()
        return model
    
    def setup_tuner(self):
        self.tuner = kt.Hyperband(
            self.build_model,
            overwrite=True,
            objective='val_loss',
            max_epochs=self.max_epochs,
            factor=3,
            directory=os.path.join(self.output_dir, "keras_tuner_autoencoder"),
            project_name="keras_tuner_autoencoder_prj"
        )
    
    def search(self, X_train):
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=15)
        
        self.tuner.search(X_train, X_train, epochs=self.max_epochs, validation_split=0.2,
                          callbacks=[early_stopping,
                                     tf.keras.callbacks.TensorBoard(log_dir=os.path.join(self.output_dir, "/tmp/tb_logs"))])
    
        self.model = self.tuner.get_best_models()[0]
    
    def reconstruct(self, X):
        if self.model is None:
            raise Exception("Model is not trained yet. Call the search method to train the model.")
        return self.model.predict(X)
    
    def compute_reconstruction_error(self, X):
        X_reconstructed = self.reconstruct(X)
        reconstruction_error = tf.keras.losses.mse(X, X_reconstructed)
        
        plt.hist(reconstruction_error.numpy(), bins=50)
        plt.xlabel("Reconstruction error")
        plt.ylabel("Frequency")
        plt.show()
        
        return reconstruction_error.numpy()
