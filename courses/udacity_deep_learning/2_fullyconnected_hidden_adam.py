# These are all the modules we'll be using later. Make sure you can import them
# before proceeding further.
from __future__ import print_function
import numpy as np
import tensorflow as tf
from six.moves import cPickle as pickle
from six.moves import range

pickle_file = 'notMNIST.pickle'

with open(pickle_file, 'rb') as f:
  save = pickle.load(f, encoding='latin1')
  train_dataset = save['train_dataset']
  train_labels = save['train_labels']
  valid_dataset = save['valid_dataset']
  valid_labels = save['valid_labels']
  test_dataset = save['test_dataset']
  test_labels = save['test_labels']

  #train_dataset = train_dataset > 0.1
  #train_dataset = train_dataset.astype(float)
  #valid_dataset = valid_dataset > 0.1
  #valid_dataset = valid_dataset.astype(float)

  del save  # hint to help gc free up memory
  print('Training set', train_dataset.shape, train_labels.shape)
  print('Validation set', valid_dataset.shape, valid_labels.shape)
  print('Test set', test_dataset.shape, test_labels.shape)

image_size = 28
num_labels = 10

def reformat(dataset, labels):
  dataset = dataset.reshape((-1, image_size * image_size)).astype(np.float32)
  # Map 0 to [1.0, 0.0, 0.0 ...], 1 to [0.0, 1.0, 0.0 ...]
  labels = (np.arange(num_labels) == labels[:,None]).astype(np.float32)
  return dataset, labels

train_dataset, train_labels = reformat(train_dataset, train_labels)
valid_dataset, valid_labels = reformat(valid_dataset, valid_labels)
test_dataset, test_labels = reformat(test_dataset, test_labels)
print('Training set', train_dataset.shape, train_labels.shape)
print('Validation set', valid_dataset.shape, valid_labels.shape)
print('Test set', test_dataset.shape, test_labels.shape)

# With gradient descent training, even this much data is prohibitive.
# Subset the training data for faster turnaround.
train_subset = 20000

HIDDEN_NODES = 1024
LEARNING_RATE = 0.0005

print('LearningRate:', LEARNING_RATE)

graph = tf.Graph()
with graph.as_default():
    # Input data.
    # Load the training, validation and test data into constants that are
    # attached to the graph.
    tf_train_dataset = tf.constant(train_dataset[:train_subset, :])
    tf_train_labels = tf.constant(train_labels[:train_subset])
    tf_valid_dataset = tf.constant(valid_dataset)
    tf_test_dataset = tf.constant(test_dataset)

    # Variables.
    # These are the parameters that we are going to be training. The weight
    # matrix will be initialized using random values following a (truncated)
    # normal distribution. The biases get initialized to zero.
    WEIGHTS = tf.Variable(tf.truncated_normal([HIDDEN_NODES, num_labels], stddev=0.05))
    BIASES = tf.Variable(tf.zeros([num_labels]))

    HIDDEN_WEIGHTS = tf.Variable(tf.truncated_normal([image_size * image_size, HIDDEN_NODES], stddev=0.05))
    HIDDEN_BIASES = tf.Variable(tf.zeros([HIDDEN_NODES]))

    """
        Compute the logits WX + b and then apply D(S(WX + b), L) on them for the hidden layer
        The relu is applied on the hidden layer nodes only
    """
    TRAIN_HIDDEN_RELU = tf.nn.relu(tf.matmul(tf_train_dataset, HIDDEN_WEIGHTS) + HIDDEN_BIASES)
    VALID_HIDDEN_RELU = tf.nn.relu(tf.matmul(tf_valid_dataset, HIDDEN_WEIGHTS) + HIDDEN_BIASES)
    TEST_HIDDEN_RELU  = tf.nn.relu(tf.matmul(tf_test_dataset,  HIDDEN_WEIGHTS) + HIDDEN_BIASES)

    # Training computation.
    # We multiply the inputs with the weight matrix, and add biases. We compute
    # the softmax and cross-entropy (it's one operation in TensorFlow, because
    # it's very common, and it can be optimized). We take the average of this
    # cross-entropy across all training examples: that's our loss.
    TRAIN_LOGITS = tf.matmul(TRAIN_HIDDEN_RELU, WEIGHTS) + BIASES
    VALID_LOGITS = tf.matmul(VALID_HIDDEN_RELU, WEIGHTS) + BIASES
    TEST_LOGITS  = tf.matmul(TEST_HIDDEN_RELU, WEIGHTS) + BIASES

    loss = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits_v2(labels=tf_train_labels, logits=TRAIN_LOGITS))

    # Optimizer.
    # We are going to find the minimum of this loss using gradient descent.
    optimizer = tf.train.AdamOptimizer(learning_rate=LEARNING_RATE).minimize(loss)

    # Predictions for the training, validation, and test data.
    # These are not part of training, but merely here so that we can report
    # accuracy figures as we train.
    train_prediction = tf.nn.softmax(TRAIN_LOGITS)

    valid_prediction = tf.nn.softmax(VALID_LOGITS)
    test_prediction = tf.nn.softmax(TEST_LOGITS)

num_steps = 501

def accuracy(predictions, labels):
  return (100.0 * np.sum(np.argmax(predictions, 1) == np.argmax(labels, 1))
          / predictions.shape[0])

with tf.Session(graph=graph) as session:
  # This is a one-time operation which ensures the parameters get initialized as
  # we described in the graph: random weights for the matrix, zeros for the
  # biases.
  tf.global_variables_initializer().run()
  print('Initialized')
  for step in range(num_steps):
    # Run the computations. We tell .run() that we want to run the optimizer,
    # and get the loss value and the training predictions returned as numpy
    # arrays.
    _, l, predictions = session.run([optimizer, loss, train_prediction])

    if (step % 100 == 0):
      print('Loss at step %d: %f' % (step, l))
      print('Training accuracy: %.1f%%' % accuracy(
        predictions, train_labels[:train_subset, :]))
      # Calling .eval() on valid_prediction is basically like calling run(), but
      # just to get that one numpy array. Note that it recomputes all its graph
      # dependencies.
      print('Validation accuracy: %.1f%%' % accuracy(valid_prediction.eval(), valid_labels))

    if (step % 100 == 0):
      print('Test accuracy: %.1f%%' % accuracy(test_prediction.eval(), test_labels))

################################################################################
