# -*- coding: utf-8 -*-
"""openai_gym_space_invaders_dqn.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IDhuYq-xZe6iOQAA8DPNhTbDzc2lt8CT

# Space Invaders
"""

!pip install gym[atari]
!pip install autorom[accept-rom-license]

!pip install pyvirtualdisplay
!apt-get install -y xvfb python-opengl ffmpeg

!apt-get install xvfb
!pip install xvfbwrapper

import numpy as np
import gym
import matplotlib.pyplot as plt
env = gym.make("SpaceInvaders-v0")
observation = env.reset()
plt.imshow(observation)
plt.show()
observation, _, _, _ = env.step(1)

import numpy as np
import gym
env = gym.make("SpaceInvaders-v0")
observation = env.reset()
prev_input = None

FIRE_ACTION = 1
RIGHT_ACTION = 2
LEFT_ACTION = 3

gamma = 0.99

x_train, y_train, rewards = [],[],[]
reward_sum = 0
episode_nb = 0

import cv2

def prepro(I):
  """prepro 210x160x3 frame into 168x168, then downscale to 84x84 1D float vector"""
  I = I[27:195] # crop to 168x160
  I = I[:,:,0]  # Convert to grayscale by taking one channel

  # Add 4 black pixels on each side to make it 168x168
  I = cv2.copyMakeBorder(I, 0, 0, 4, 4, cv2.BORDER_CONSTANT, value=0)

  # Downscale to 84x84
  I = cv2.resize(I, (84, 84), interpolation=cv2.INTER_AREA)

  I[I == 0] = 0 # You may need to change this value based on the actual background color in Space Invaders
  I[I != 0] = 1  # Set all other (non-zero) pixels to 1

  return I.astype(np.float).ravel()

# Show preprocessed
obs_preprocessed = prepro(observation).reshape(84, 84)
plt.imshow(obs_preprocessed, cmap='gray')
plt.show()

# Number of steps you want to play
num_steps = 500

env.reset()

for _ in range(num_steps):
    action = env.action_space.sample()  # Taking random actions
    observation, _, _, _ = env.step(action)

# Preprocess the final observation
obs_preprocessed = prepro(observation).reshape(84, 84)

# Show preprocessed observation
plt.imshow(obs_preprocessed, cmap='gray')
plt.show()

def discount_rewards(r, gamma):
  """take 1D float array of rewards and compute discounted reward"""
  r = np.array(r)
  discounted_r = np.zeros_like(r)
  running_add = 0

  for t in reversed(range(0, r.size)):
    if r[t] != 0:
      running_add = 0 # if the game ended (in Pong), reset
    running_add = running_add * gamma + r[t]
    discounted_r[t] = running_add

  discounted_r -= np.mean(discounted_r) #normalizing the result
  discounted_r /= np.std(discounted_r) #idem using standar deviation
  return discounted_r

# import necessary modules from keras
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Reshape
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import Flatten
from tensorflow.keras.models import Sequential
import tensorflow.keras
from tensorflow.keras.layers import InputLayer
from tensorflow.keras.optimizers import Adam

# Input dimension is 7056 after preprocessing (84 * 84)
input_dim = 84 * 84

# Initialize the model
model = Sequential()

# Add a hidden layer with 200 units
model.add(Dense(units=200, input_dim=input_dim, activation='relu', kernel_initializer='glorot_uniform'))

# Add an output layer with 3 units (one for each action)
model.add(Dense(units=3, activation='softmax', kernel_initializer='RandomNormal'))

# Compile the model
model.compile(loss='categorical_crossentropy', optimizer=Adam(), metrics=['accuracy'])

# Print the model summary
print(model.summary())

num_epochs = 50

import time

def print_epochs(epochs, elapsed_time):
    print("==================================================")
    print(f"Epochs: {epochs}")
    print(f"Time elapsed till this epoch: {elapsed_time} seconds")
    print("==================================================")

history = []
observation = env.reset()
prev_input = None

time_history = []
start_time = time.time()  # Initial time
epochs = 0
print_epochs(epochs, 0)

# File to store log of times
with open(f"time_epochs_{num_epochs}.txt", "w") as time_file:
    # Main training loop
    while True:
        if epochs == num_epochs:
            break

        cur_input = prepro(observation)
        x = cur_input - prev_input if prev_input is not None else np.zeros(84 * 84)
        prev_input = cur_input

        proba = model.predict(np.expand_dims(x, axis=1).T)
        action = np.random.choice([FIRE_ACTION, RIGHT_ACTION, LEFT_ACTION], p=proba.ravel())
        y = np.zeros(3)
        y[action - 1] = 1

        x_train.append(x)
        y_train.append(y)

        observation, reward, done, info = env.step(action)
        rewards.append(reward)
        reward_sum += reward

        if done:
            history.append(reward_sum)
            print(f'At the end of episode {episode_nb}, the total reward was: {reward_sum}')

            epochs += 1
            elapsed_time = time.time() - start_time
            time_history.append(elapsed_time)
            print_epochs(epochs, elapsed_time)

            # Log the time to the file
            time_file.write(f"Epoch {epochs}: {elapsed_time}s")

            if episode_nb >= 3000 and reward_sum >= -12:
                break
            else:
                episode_nb += 1
                model.fit(x=np.vstack(x_train), y=np.vstack(y_train), verbose=1, sample_weight=discount_rewards(rewards, gamma))

                x_train, y_train, rewards = [], [], []
                observation = env.reset()
                reward_sum = 0
                prev_input = None

plt.plot(history)
plt.show()

with open(f"history_epochs_{num_epochs}.txt", "w") as history_file:
  for history_item in history:
    history_file.write(f"{history_item}\n")

model.save(f'space_invaders_epochs_{num_epochs}.h5')

from tensorflow.keras.models import load_model

loaded_model = load_model(f'space_invaders_epochs_{num_epochs}.h5')

import gym
from gym import logger as gymlogger
from gym.wrappers.record_video import RecordVideo
from pyvirtualdisplay import Display
import numpy as np
import glob
import io
import base64
from IPython.display import HTML
from IPython import display as ipythondisplay

# Utility functions for video recording
def show_video():
  mp4list = glob.glob('video/*.mp4')
  if len(mp4list) > 0:
    mp4 = mp4list[0]
    video = io.open(mp4, 'r+b').read()
    encoded = base64.b64encode(video)
    ipythondisplay.display(HTML(data='''<video alt="test" autoplay loop controls style="height: 400px;">
                <source src="data:video/mp4;base64,{0}" type="video/mp4" />
             </video>'''.format(encoded.decode('ascii'))))
  else:
    print("Could not find video")

def wrap_env(env):
  env = RecordVideo(env, './video')
  return env

# Initialize display
display = Display(visible=0, size=(1400, 900))
display.start()

# Create Space Invaders environment and wrap it for video recording
env = wrap_env(gym.make('SpaceInvaders-v0'))
observation = env.reset()
new_observation = observation
prev_input = None
done = False

while True:
  # Preprocess the observation
  cur_input = prepro(observation)
  x = cur_input - prev_input if prev_input is not None else np.zeros(84 * 84)
  prev_input = cur_input

  # Get action probabilities from the model
  proba = model.predict(np.expand_dims(x, axis=0))

  # Sample an action based on probabilities
  action = np.random.choice([FIRE_ACTION, RIGHT_ACTION, LEFT_ACTION], p=proba.ravel())

  # Render the environment
  env.render()

  # Take the selected action
  observation = new_observation
  new_observation, reward, done, info = env.step(action)

  if done:
    break

# Close environment and display video
env.close()
show_video()

# Demo of how the action is selected from the policy
proba = model.predict(np.expand_dims(x, axis=1).T)
action = np.random.choice([FIRE_ACTION, RIGHT_ACTION, LEFT_ACTION], p=proba.ravel())
print(f"proba: {proba}")
print(f"action: {action}")