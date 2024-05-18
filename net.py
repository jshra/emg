import tensorflow as tf
from tensorflow.keras import layers
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.utils import Sequence
#%%
alldata = np.genfromtxt('t1.ASC', delimiter = ';', skip_header=8 , autostrip = True)
data = alldata[:49800,1:7]
test = alldata[49800:50000,1:7]
print(data[:,:5].shape)
print(data[:,-1].shape)
#%%
class TSGenerator(Sequence):
    def __init__(self, data, window_size, batch_size, step_size=1):
        self.data = data
        self.window_size = window_size
        self.batch_size = batch_size
        self.step_size = step_size
        self.indices = np.arange(0, len(data) - window_size, step_size)
    
    def __len__(self):
        return int(np.ceil(len(self.indices) / self.batch_size))
    
    def __getitem__(self, idx):
        batch_indices = self.indices[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_data = np.array([self.data[i:i + self.window_size] for i in batch_indices])
        
        input_data = np.array([sample[:, :5] for sample in batch_data])
        labels = np.array([np.mean(sample[:, -1]) for sample in batch_data])
        
        return input_data, labels
    
    def on_epoch_end(self):
        pass
    
class SelfAttention(tf.keras.layers.Layer):
    def __init__(self, units, **kwargs):
        super().__init__()
        self.mha = tf.keras.layers.MultiHeadAttention(key_dim=units, num_heads=4, **kwargs)
        self.dropout = tf.keras.layers.Dropout(0.1)
        self.layernorm = tf.keras.layers.LayerNormalization()
        self.add = tf.keras.layers.Add()
    def call(self, x):
       attn_output = self.mha(query=x, value=x)
       attn_output = self.dropout(attn_output)
       x = self.add([x, attn_output])
       x = self.layernorm(x)
       return x
   
class FeedForward(tf.keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__()
        self.layernorm = tf.keras.layers.LayerNormalization()
        self.conv1 = tf.keras.layers.Conv1D(filters=3, kernel_size=1, activation = 'relu')
        self.dropout = tf.keras.layers.Dropout(0.1)
        self.conv2 = tf.keras.layers.Conv1D(filters=5, kernel_size=1)
        self.add = tf.keras.layers.Add()
    def call(self, x):
        out = self.layernorm(x)
        out = self.conv1(out)
        out = self.dropout(out)
        out = self.conv2(out)
        
        x = self.add([x, out])
        return x
    
class MLP(tf.keras.layers.Layer):
    def __init__(self, units, **kwargs):
        super().__init__()
        self.mlp = tf.keras.layers.Dense(units, activation='relu')
        self.dropout = tf.keras.layers.Dropout(0.1)
    def call(self, x):
        x = self.mlp(x)
        x = self.dropout(x)
        return x
       
class Regression_block(tf.keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__()
        self.mlp1 = MLP(128)
        self.mlp2 = MLP(128)
        self.final = tf.keras.layers.Dense(1, activation='relu')
        self.GAP = tf.keras.layers.GlobalAveragePooling1D()
    def call(self, x):
        x = self.GAP(x)
        x = self.mlp1(x)
        x = self.mlp2(x)
        x = self.final(x)
        return x

#%%
input_layer = tf.keras.Input(shape=(200,5))
mha_layer = SelfAttention(200)(input_layer)
ff_layer = FeedForward()(mha_layer)
output_layer = Regression_block()(ff_layer)
#%%

model = tf.keras.Model(input_layer, output_layer)
model.summary()
model.compile(optimizer='rmsprop', loss='mean_squared_error')
#%%
train_generator = TSGenerator(data, window_size = 200, batch_size = 32, step_size=20)
model.fit(train_generator, epochs=10)
#%%
tdata = test[:,:5]
tlabel = np.mean(test[:,-1])

#%%
model.predict(np.expand_dims(tdata, 0))



