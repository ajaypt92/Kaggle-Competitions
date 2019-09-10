import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sb
from datetime import datetime

from sklearn.cluster import *
from sklearn.cross_validation import *
from sklearn.decomposition import *
from sklearn.ensemble import *
from sklearn.feature_extraction import *
from sklearn.feature_selection import *
from sklearn.grid_search import *
from sklearn.learning_curve import *
from sklearn.linear_model import *
from sklearn.manifold import *
from sklearn.metrics import *
from sklearn.naive_bayes import *
from sklearn.preprocessing import *
from sklearn.svm import *

from xgboost import *
from keras.callbacks import *
from keras.layers.core import *
from keras.layers.normalization import *
from keras.layers.advanced_activations import *
from keras.models import *
from keras.optimizers import *


class Logger(object):
    def __init__(self, path):
        self.terminal = sys.stdout
        self.log = open(path, 'a')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.log.flush()

    def close(self):
        self.log.close()


class AllLabelEncoder(object):
    def __init__(self):
        print('TODO')

    def fit(self):
        print('TODO')

    def transform(self):
        print('TODO')

    def fit_transform(self):
        print('TODO')


class FactorToNumeric(object):
    def __init__(self, categorical_features=None, metric='mean'):
        self.categorical_features = categorical_features
        self.metric = metric
        self.feature_map_ = {}

    def fit(self, X, y):
        for i in self.categorical_features:
            self.feature_map_[i] = {}
            distinct = list(np.unique(X[:, i]))
            for j in distinct:
                if self.metric == 'mean':
                    self.feature_map_[i][j] = y[X[:, i] == j].mean()
                elif self.metric == 'median':
                    self.feature_map_[i][j] = y[X[:, i] == j].median()
                elif self.metric == 'std':
                    self.feature_map_[i][j] = y[X[:, i] == j].std()
                else:
                    raise Exception('Metric not not recognized.')

    def transform(self, X):
        X_trans = np.copy(X)
        for i in self.categorical_features:
            distinct = list(np.unique(X_trans[:, i]))
            for j in distinct:
                X_trans[X_trans[:, i] == j, i] = self.feature_map_[i][j]

        return X_trans

    def fit_transform(self, X, y):
        self.fit(X, y)
        return self.transform(X)


code_dir = '/home/john/git/kaggle/PropertyInspection/'
data_dir = '/home/john/data/property-inspection/'
os.chdir(code_dir)
logger = Logger(data_dir + 'output.txt')
sys.stdout = logger
# sys.stdout = logger.terminal
# logger.close()


def load_csv_data(directory, filename, dtype=None, index=None, convert_to_date=False):
    """
    Load a csv data file into a data frame, setting the index as appropriate.
    """
    data = pd.read_csv(directory + filename, sep=',', dtype=dtype)

    if index is not None:
        if convert_to_date:
            if type(index) is str:
                data[index] = data[index].convert_objects(convert_dates='coerce')
            else:
                for key in index:
                    data[key] = data[key].convert_objects(convert_dates='coerce')

        data = data.set_index(index)

    print('Data file ' + filename + ' loaded successfully.')

    return data


def load_model(filename):
    """
    Load a previously training model from disk.
    """
    model_file = open(filename, 'rb')
    model = pickle.load(model_file)
    model_file.close()

    return model


def save_model(model, filename):
    """
    Persist a trained model to disk.
    """
    model_file = open(filename, 'wb')
    pickle.dump(model, model_file)
    model_file.close()


def gini_score(y, y_pred):
    """
    Computes the Gini coefficient between a set of predictions and true labels.
    """
    # check and get number of samples
    assert y.shape == y_pred.shape
    n_samples = y.shape[0]

    # sort rows on prediction column (from largest to smallest)
    arr = np.array([y, y_pred]).transpose()
    true_order = arr[arr[:, 0].argsort()][::-1, 0]
    pred_order = arr[arr[:, 1].argsort()][::-1, 0]

    # get Lorenz curves
    L_true = np.cumsum(true_order) / np.sum(true_order)
    L_pred = np.cumsum(pred_order) / np.sum(pred_order)
    L_ones = np.linspace(0, 1, n_samples)

    # get Gini coefficients (area between curves)
    G_true = np.sum(L_ones - L_true)
    G_pred = np.sum(L_ones - L_pred)

    # normalize to true Gini coefficient
    return G_pred / G_true


def score(y, y_pred, metric):
    """
    Calculates a score for the given predictions using the provided metric.
    """
    y_pred = y_pred.ravel()
    assert y.shape == y_pred.shape

    if metric == 'accuracy':
        return accuracy_score(y, y_pred)
    elif metric == 'f1':
        return f1_score(y, y_pred)
    elif metric == 'log_loss':
        return log_loss(y, y_pred)
    elif metric == 'mean_absolute_error':
        return mean_absolute_error(y, y_pred)
    elif metric == 'mean_squared_error':
        return mean_squared_error(y, y_pred)
    elif metric == 'r2':
        return r2_score(y, y_pred)
    elif metric == 'roc_auc':
        return roc_auc_score(y, y_pred)
    elif metric == 'gini':
        return gini_score(y, y_pred)


def predict_score(X, y, model, metric):
    """
    Predicts and scores the model's performance and returns the result.
    """
    if metric is not None:
        y_pred = model.predict(X)
        return score(y, y_pred, metric)
    else:
        return model.score(X, y)


def generate_features(data):
    """
    Generates new derived features to add to the data set for model training.
    """
    return data


def process_data(directory, train_file, test_file, label_index, column_offset, ex_generate_features):
    """
    Reads in training data and prepares numpy arrays.
    """
    train_data = load_csv_data(directory, train_file, index='Id')
    test_data = load_csv_data(directory, test_file, index='Id')

    if ex_generate_features:
        train_data = generate_features(train_data)
        test_data = generate_features(test_data)

    X = train_data.iloc[:, column_offset:].values
    y = train_data.iloc[:, label_index].values
    X_test = test_data.values

    # label encode the categorical variables
    for i in range(X.shape[1]):
        if type(X[0, i]) is str:
            le = LabelEncoder()
            le.fit(X[:, i])
            X[:, i] = le.transform(X[:, i])
            X_test[:, i] = le.transform(X_test[:, i])

    # # Training data for the 2nd level model
    # stacker_train = load_csv_data(data_dir, 'save_stacker_train.csv')
    # stacker_label = load_csv_data(data_dir, 'save_stacker_label.csv')
    # stacker_test = load_csv_data(data_dir, 'save_stacker_test.csv')
    # X = stacker_train.iloc[:, 1:4].values
    # y = stacker_label.iloc[:, 1].values
    # X_test = stacker_test.iloc[:, 1:4].values

    print('Data processing complete.')

    return train_data, test_data, X, y, X_test


def fit_transforms(X, y, transforms):
    """
    Fits new transformations from a data set.
    """
    for i, trans in enumerate(transforms):
        if trans is not None:
            X = trans.fit_transform(X, y)
        transforms[i] = trans

    return transforms


def apply_transforms(X, transforms):
    """
    Applies pre-computed transformations to a data set.
    """
    for trans in transforms:
        if trans is not None:
            X = trans.transform(X)

    return X


def visualize_variable_relationships(train_data, viz_type, quantitative_vars, category_vars=None):
    """
    Generates plots showing the relationship between several variables.
    """
    # compare the continuous variable distributions using a violin plot
    sub_data = train_data[quantitative_vars]
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    sb.violinplot(sub_data, ax=ax)
    fig.tight_layout()

    # if categorical variables were provided, visualize the quantitative distributions by category
    if category_vars is not None:
        fig, ax = plt.subplots(len(quantitative_vars), len(category_vars), figsize=(16, 12))
        for i, var in enumerate(quantitative_vars):
            for j, cat in enumerate(category_vars):
                sb.violinplot(train_data[var], train_data[cat], ax=ax[i, j])
        fig.tight_layout()

    # generate plots to directly compare the variables
    if category_vars is None:
        if len(quantitative_vars) == 2:
            sb.jointplot(quantitative_vars[0], quantitative_vars[1], train_data, kind=viz_type, size=16)
        else:
            sb.pairplot(train_data, vars=quantitative_vars, kind='scatter',
                        diag_kind='kde', size=16 / len(quantitative_vars))
    else:
        if len(quantitative_vars) == 1:
            if len(category_vars) == 1:
                sb.factorplot(category_vars[0], quantitative_vars[0], None,
                              train_data, kind='auto', size=16)
            else:
                sb.factorplot(category_vars[0], quantitative_vars[0], category_vars[1],
                              train_data, kind='auto', size=16)
        if len(quantitative_vars) == 2:
            if len(category_vars) == 1:
                sb.lmplot(quantitative_vars[0], quantitative_vars[1], train_data,
                          col=None, row=category_vars[0], size=16)
            else:
                sb.lmplot(quantitative_vars[0], quantitative_vars[1], train_data,
                          col=category_vars[0], row=category_vars[1], size=16)
        else:
            sb.pairplot(train_data, hue=category_vars[0], vars=quantitative_vars, kind='scatter',
                        diag_kind='kde', size=16 / len(quantitative_vars))


def visualize_feature_distributions(train_data, viz_type, plot_size):
    """
    Generates feature distribution plots (histogram or kde) for each feature.
    """
    if viz_type == 'hist':
        hist = True
        kde = False
    else:
        hist = False
        kde = True

    num_features = len(train_data.columns)
    num_plots = num_features / plot_size if num_features % plot_size == 0 else num_features / plot_size + 1

    for i in range(num_plots):
        fig, ax = plt.subplots(4, 4, figsize=(20, 10))
        for j in range(plot_size):
            index = (i * plot_size) + j
            if index < num_features:
                if type(train_data.iloc[0, index]) is str:
                    sb.countplot(x=train_data.columns[index], data=train_data, ax=ax[j / 4, j % 4])
                else:
                    sb.distplot(train_data.iloc[:, index], hist=hist, kde=kde, label=train_data.columns[index],
                                ax=ax[j / 4, j % 4], kde_kws={"shade": True})
        fig.tight_layout()


def visualize_correlations(train_data):
    """
    Generates a correlation matrix heat map.
    """
    fig, ax = plt.subplots(figsize=(16, 10))
    colormap = sb.blend_palette(sb.color_palette('coolwarm'), as_cmap=True)
    if len(train_data.columns) < 30:
        sb.corrplot(train_data, annot=True, sig_stars=False, diag_names=True, cmap=colormap, ax=ax)
    else:
        sb.corrplot(train_data, annot=False, sig_stars=False, diag_names=False, cmap=colormap, ax=ax)
    fig.tight_layout()


def visualize_sequential_relationships(train_data, plot_size, smooth=None, window=1):
    """
    Generates line plots to visualize sequential data.  Assumes the data frame index is time series.
    """
    train_data.index.name = None
    num_features = len(train_data.columns)
    num_plots = num_features / plot_size if num_features % plot_size == 0 else num_features / plot_size + 1

    for i in range(num_plots):
        fig, ax = plt.subplots(4, 4, sharex=True, figsize=(20, 10))
        for j in range(plot_size):
            index = (i * plot_size) + j
            if index < num_features:
                if index != 3:  # this column is all 0s in the bike set
                    if smooth == 'mean':
                        train_data.iloc[:, index] = pd.rolling_mean(train_data.iloc[:, index], window)
                    elif smooth == 'var':
                        train_data.iloc[:, index] = pd.rolling_var(train_data.iloc[:, index], window)
                    elif smooth == 'skew':
                        train_data.iloc[:, index] = pd.rolling_skew(train_data.iloc[:, index], window)
                    elif smooth == 'kurt':
                        train_data.iloc[:, index] = pd.rolling_kurt(train_data.iloc[:, index], window)

                    train_data.iloc[:, index].plot(ax=ax[j / 4, j % 4], kind='line', legend=False,
                                                   title=train_data.columns[index])
        fig.tight_layout()


def visualize_transforms(X, y, model_type, n_components, transforms):
    """
    Generates plots to visualize the data transformed by a non-linear manifold algorithm.
    """
    transforms = fit_transforms(X, y, transforms)
    X = apply_transforms(X, transforms)

    if model_type == 'classification':
        class_count = np.count_nonzero(np.unique(y))
        colors = sb.color_palette('hls', class_count)

        for i in range(n_components - 1):
            fig, ax = plt.subplots(figsize=(16, 10))
            for j in range(class_count):
                ax.scatter(X[y == j, i], X[y == j, i + 1], s=50, c=colors[j], label=j)
            ax.set_title('Components ' + str(i + 1) + ' and ' + str(i + 2))
            ax.legend()
            fig.tight_layout()
    else:
        for i in range(n_components - 1):
            fig, ax = plt.subplots(figsize=(16, 10))
            sc = ax.scatter(X[:, i], X[:, i + 1], s=50, c=y, cmap='Reds')
            ax.set_title('Components ' + str(i + 1) + ' and ' + str(i + 2))
            ax.legend()
            fig.colorbar(sc)
            fig.tight_layout()


def define_model(model_type, algorithm):
    """
    Defines and returns a model object of the designated type.
    """
    model = None

    if model_type == 'classification':
        if algorithm == 'bayes':
            model = GaussianNB()
        elif algorithm == 'logistic':
            model = LogisticRegression(penalty='l2', C=1.0)
        elif algorithm == 'svm':
            model = SVC(C=1.0, kernel='rbf', shrinking=True, probability=False, cache_size=200)
        elif algorithm == 'sgd':
            model = SGDClassifier(loss='hinge', penalty='l2', alpha=0.0001, n_iter=1000, shuffle=False, n_jobs=-1)
        elif algorithm == 'forest':
            model = RandomForestClassifier(n_estimators=10, criterion='gini', max_features='auto', max_depth=None,
                                           min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'xt':
            model = ExtraTreesClassifier(n_estimators=10, criterion='gini', max_features='auto', max_depth=None,
                                         min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'boost':
            model = GradientBoostingClassifier(loss='deviance', learning_rate=0.1, n_estimators=100, subsample=1.0,
                                               min_samples_split=2, min_samples_leaf=1, max_depth=3, max_features=None,
                                               max_leaf_nodes=None)
        elif algorithm == 'xgb':
            model = XGBClassifier(max_depth=3, learning_rate=0.1, n_estimators=100, silent=True,
                                  objective='multi:softmax', gamma=0, min_child_weight=1, max_delta_step=0,
                                  subsample=1.0, colsample_bytree=1.0, base_score=0.5, seed=0, missing=None)
        else:
            print('No model defined for ' + algorithm)
            exit()
    else:
        if algorithm == 'ridge':
            model = Ridge(alpha=1.0)
        elif algorithm == 'svm':
            model = SVR(C=1.0, kernel='rbf', shrinking=True, cache_size=200)
        elif algorithm == 'sgd':
            model = SGDRegressor(loss='squared_loss', penalty='l2', alpha=0.0001, n_iter=1000, shuffle=False)
        elif algorithm == 'forest':
            model = RandomForestRegressor(n_estimators=10, criterion='mse', max_features='auto', max_depth=None,
                                          min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'xt':
            model = ExtraTreesRegressor(n_estimators=10, criterion='mse', max_features='auto', max_depth=None,
                                        min_samples_split=2, min_samples_leaf=1, max_leaf_nodes=None, n_jobs=-1)
        elif algorithm == 'boost':
            model = GradientBoostingRegressor(loss='ls', learning_rate=0.1, n_estimators=100, subsample=1.0,
                                              min_samples_split=2, min_samples_leaf=1, max_depth=3, max_features=None,
                                              max_leaf_nodes=None)
        elif algorithm == 'xgb':
            # model = XGBRegressor(max_depth=3, learning_rate=0.01, n_estimators=1000, silent=True,
            #                      objective='reg:linear', gamma=0, min_child_weight=1, max_delta_step=0,
            #                      subsample=1.0, colsample_bytree=1.0, base_score=0.5, seed=0, missing=None)
            xg = XGBRegressor(max_depth=7, learning_rate=0.005, n_estimators=1800, silent=True,
                              objective='reg:linear', gamma=0, min_child_weight=1, max_delta_step=0,
                              subsample=0.9, colsample_bytree=0.8, base_score=0.5, seed=0, missing=None)
            model = BaggingRegressor(base_estimator=xg, n_estimators=10, max_samples=1.0, max_features=1.0,
                                     bootstrap=True, bootstrap_features=False)
        else:
            print('No model defined for ' + algorithm)
            exit()

    return model


def define_nn_model(X, y, transforms):
    """
    Defines and returns a Keras neural network model.
    """
    transforms = fit_transforms(X, y, transforms)
    X = apply_transforms(X, transforms)

    input_size = X.shape[1]
    layer_size = 128
    output_size = 1

    # uniform, lecun_uniform, normal, identity, orthogonal, zero, glorot_normal, glorot_uniform, he_normal, he_uniform
    init_method = 'glorot_uniform'

    # softmax, softplus, relu, tanh, sigmoid, hard_sigmoid, linear
    activation_method = 'linear'

    # mse, mae, mape, msle, squared_hinge, hinge, binary_crossentropy, categorical_crossentropy
    loss_function = 'mse'

    model = Sequential()
    model.add(Dense(input_size, layer_size, init=init_method))
    model.add(PReLU((layer_size,)))
    model.add(BatchNormalization((layer_size,)))
    model.add(Dropout(0.5))

    model.add(Dense(layer_size, layer_size, init=init_method))
    model.add(PReLU((layer_size,)))
    model.add(BatchNormalization((layer_size,)))
    model.add(Dropout(0.5))

    model.add(Dense(layer_size, output_size, init=init_method))
    model.add(Activation(activation_method))

    optimizer = SGD(lr=0.1, momentum=0.9, decay=1e-6, nesterov=True)
    # optimizer = Adagrad()
    # optimizer = Adadelta()
    # optimizer = RMSprop()
    # optimizer = Adam()

    model.compile(loss=loss_function, optimizer=optimizer)

    return model


def define_nn_model_detailed(input_size, layer_size, output_size, n_hidden_layers, init_method, loss_function,
                             input_activation, hidden_activation, output_activation, use_batch_normalization,
                             input_dropout, hidden_dropout, optimization_method):
    """
    Defines and returns a Keras neural network model.
    """
    model = Sequential()

    # add input layer
    model.add(Dense(input_size, layer_size, init=init_method))

    if input_activation == 'prelu':
        model.add(PReLU((layer_size,)))
    else:
        model.add(Activation(input_activation))

    if use_batch_normalization:
        model.add(BatchNormalization((layer_size,)))

    model.add(Dropout(input_dropout))

    # add hidden layers
    for i in range(n_hidden_layers):
        model.add(Dense(layer_size, layer_size, init=init_method))

        if hidden_activation == 'prelu':
            model.add(PReLU((layer_size,)))
        else:
            model.add(Activation(hidden_activation))

        if use_batch_normalization:
            model.add(BatchNormalization((layer_size,)))

        model.add(Dropout(hidden_dropout))

    # add output layer
    model.add(Dense(layer_size, output_size, init=init_method))
    model.add(Activation(output_activation))

    # configure optimization method
    if optimization_method == 'sgd':
        optimizer = SGD(lr=0.1, momentum=0.9, decay=1e-6, nesterov=True)
    elif optimization_method == 'adagrad':
        optimizer = Adagrad()
    elif optimization_method == 'adadelta':
        optimizer = Adadelta()
    elif optimization_method == 'rmsprop':
        optimizer = RMSprop()
    elif optimization_method == 'adam':
        optimizer = Adam()
    else:
        raise Exception('Optimization method not recognized.')

    model.compile(loss=loss_function, optimizer=optimizer)

    return model


def train_model(X, y, algorithm, model, metric, transforms, early_stopping):
    """
    Trains a new model using the training data.
    """
    if algorithm == 'xgb':
        return train_xgb_model(X, y, model, metric, transforms, early_stopping)
    elif algorithm == 'nn':
        return train_nn_model(X, y, model, metric, transforms, early_stopping)
    else:
        t0 = time.time()
        transforms = fit_transforms(X, y, transforms)
        X = apply_transforms(X, transforms)
        model.fit(X, y)
        t1 = time.time()
        print('Model trained in {0:3f} s.'.format(t1 - t0))
    
        print('Model hyper-parameters:')
        print(model.get_params())
    
        print('Calculating training score...')
        model_score = predict_score(X, y, model, metric)
        print('Training score ='), model_score
    
        return model


def train_xgb_model(X, y, model, metric, transforms, early_stopping):
    """
    Trains a new model XGB using the training data.
    """
    t0 = time.time()

    if early_stopping:
        X_train, X_eval, y_train, y_eval = train_test_split(X, y, test_size=0.1)
        transforms = fit_transforms(X_train, y_train, transforms)
        X_train = apply_transforms(X_train, transforms)
        X_eval = apply_transforms(X_eval, transforms)
        model.fit(X_train, y_train, eval_set=[(X_eval, y_eval)], eval_metric='rmse',
                  early_stopping_rounds=100)
        print('Best iteration found: ' + str(model.best_iteration))

        print('Re-fitting at the new stopping point...')
        model.n_estimators = model.best_iteration
        transforms = fit_transforms(X, y, transforms)
        X = apply_transforms(X, transforms)
        model.fit(X, y)
    else:
        transforms = fit_transforms(X, y, transforms)
        X = apply_transforms(X, transforms)
        model.fit(X, y)

    t1 = time.time()
    print('Model trained in {0:3f} s.'.format(t1 - t0))

    print('Model hyper-parameters:')
    print(model.get_params())

    print('Calculating training score...')
    model_score = predict_score(X, y, model, metric)
    print('Training score ='), model_score

    return model


def train_nn_model(X, y, model, metric, transforms, early_stopping):
    """
    Trains a new Keras model using the training data.
    """
    t0 = time.time()
    X_train = None
    X_eval = None
    y_train = None
    y_eval = None

    print('Beginning training...')
    if early_stopping:
        X_train, X_eval, y_train, y_eval = train_test_split(X, y, test_size=0.1)
        transforms = fit_transforms(X_train, y_train, transforms)
        X_train = apply_transforms(X_train, transforms)
        X_eval = apply_transforms(X_eval, transforms)
        # eval_monitor = EarlyStopping(monitor='val_loss', patience=10, verbose=0)
        # history = model.fit(X_train, y_train, batch_size=128, nb_epoch=100, verbose=0,
        #                     validation_data=(X_eval, y_eval), shuffle=True, callbacks=[eval_monitor])
        history = model.fit(X_train, y_train, batch_size=128, nb_epoch=100, verbose=0,
                            validation_data=(X_eval, y_eval), shuffle=True)
    else:
        transforms = fit_transforms(X, y, transforms)
        X = apply_transforms(X, transforms)
        history = model.fit(X, y, batch_size=128, nb_epoch=100, verbose=0, shuffle=True, callbacks=[])

    t1 = time.time()
    print('Model trained in {0:3f} s.'.format(t1 - t0))

    print('Model hyper-parameters:')
    print(model.get_config())

    print('Min eval loss ='), min(history.history['val_loss'])
    print('Min eval epoch ='), min(enumerate(history.history['loss']), key=lambda x: x[1])[0] + 1

    if early_stopping:
        print('Calculating training score...')
        train_score = predict_score(X_train, y_train, model, metric)
        print('Training score ='), train_score

        print('Calculating evaluation score...')
        eval_score = predict_score(X_eval, y_eval, model, metric)
        print('Evaluation score ='), eval_score
    else:
        print('Calculating training score...')
        train_score = predict_score(X, y, model, metric)
        print('Training score ='), train_score

    return model, history


def visualize_feature_importance(train_data, model, column_offset):
    """
    Generates a feature importance plot.  Requires a trained random forest or gradient boosting model.
    Does not work properly if transformations are applied to training data that expands the number
    of features.
    """
    importance = model.feature_importances_
    importance = 100.0 * (importance / importance.max())
    importance = importance[0:30] if len(train_data.columns) > 30 else importance
    sorted_idx = np.argsort(importance)
    pos = np.arange(sorted_idx.shape[0])

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_title('Variable Importance')
    ax.barh(pos, importance[sorted_idx], align='center')
    ax.set_yticks(pos)
    ax.set_yticklabels(train_data.columns[sorted_idx + column_offset])
    ax.set_xlabel('Relative Importance')

    fig.tight_layout()


def cross_validate(X, y, algorithm, model, metric, transforms, n_folds):
    """
    Performs manual cross-validation to estimate the true performance of the model.
    """
    t0 = time.time()
    y_pred = np.array([])
    y_true = np.array([])
    
    folds = list(KFold(y.shape[0], n_folds=n_folds, shuffle=True, random_state=1337))
    for i, (train_index, eval_index) in enumerate(folds):
        print('Starting fold {0}...'.format(i + 1))
        X_train = X[train_index]
        y_train = y[train_index]
        X_eval = X[eval_index]
        y_eval = y[eval_index]
        
        transforms = fit_transforms(X_train, y_train, transforms)
        X_train = apply_transforms(X_train, transforms)
        X_eval = apply_transforms(X_eval, transforms)

        if algorithm == 'nn':
            model.fit(X_train, y_train, batch_size=128, nb_epoch=100, verbose=0,
                      validation_data=(X_eval, y_eval), shuffle=True)
        elif algorithm == 'xgb':
            model.fit(X_train, y_train)

        y_pred = np.append(y_pred, model.predict(X_eval))
        y_true = np.append(y_true, y_eval)

    t1 = time.time()
    print('Cross-validation completed in {0:3f} s.'.format(t1 - t0))
    
    cross_validation_score = score(y_true, y_pred, metric)
    print('Cross-validation score ='), cross_validation_score

    return cross_validation_score


def sequence_cross_validate(X, y, model, metric, transforms, n_folds, strategy='traditional',
                            window_type='cumulative', min_window=0, forecast_range=1, plot=False):
    """
    Performs time series cross-validation to estimate the true performance of the model.
    """
    scores = []
    train_count = len(X)

    if strategy == 'walk-forward':
        n_folds = train_count - min_window - forecast_range
        fold_size = 1
    else:
        fold_size = train_count / n_folds

    t0 = time.time()
    for i in range(n_folds):
        if window_type == 'fixed':
            fold_start = i * fold_size
        else:
            fold_start = 0

        fold_end = (i + 1) * fold_size + min_window
        fold_train_end = fold_end - forecast_range

        X_train, X_eval = X[fold_start:fold_train_end, :], X[fold_train_end:fold_end, :]
        y_train, y_eval = y[fold_start:fold_train_end], y[fold_train_end:fold_end]

        transforms = fit_transforms(X_train, y_train, transforms)
        X_train = apply_transforms(X_train, transforms)
        X_eval = apply_transforms(X_eval, transforms)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_eval)
        scores.append(score(y, y_pred, metric))

        if plot is True:
            fig, ax = plt.subplots(figsize=(16, 10))
            ax.set_title('Estimation Error')
            ax.plot(y_pred - y_eval)
            fig.tight_layout()

    t1 = time.time()
    print('Cross-validation completed in {0:3f} s.'.format(t1 - t0))

    return np.mean(scores)


def plot_learning_curve(X, y, model, metric, transforms, n_folds):
    """
    Plots a learning curve showing model performance against both training and
    validation data sets as a function of the number of training samples.
    """
    transforms = fit_transforms(X, y, transforms)
    X = apply_transforms(X, transforms)

    t0 = time.time()
    train_sizes, train_scores, test_scores = learning_curve(model, X, y, scoring=metric, cv=n_folds, n_jobs=1)
    train_scores_mean = np.mean(train_scores, axis=1)
    train_scores_std = np.std(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    test_scores_std = np.std(test_scores, axis=1)

    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_title('Learning Curve')
    ax.set_xlabel('Training Examples')
    ax.set_ylabel('Score')
    ax.fill_between(train_sizes, train_scores_mean - train_scores_std, train_scores_mean + train_scores_std,
                    alpha=0.1, color='b')
    ax.fill_between(train_sizes, test_scores_mean - test_scores_std, test_scores_mean + test_scores_std,
                    alpha=0.1, color='r')
    ax.plot(train_sizes, train_scores_mean, 'o-', color='b', label='Training score')
    ax.plot(train_sizes, test_scores_mean, 'o-', color='r', label='Cross-validation score')
    ax.legend(loc='best')
    fig.tight_layout()
    t1 = time.time()
    print('Learning curve generated in {0:3f} s.'.format(t1 - t0))


def parameter_search(X, y, algorithm, model, metric, transforms, n_folds):
    """
    Performs an exhaustive search over the specified model parameters.
    """
    if algorithm == 'xgb':
        xbg_parameter_search(X, y, metric)
    elif algorithm == 'nn':
        nn_parameter_search(X, y, metric)
    else:
        transforms = fit_transforms(X, y, transforms)
        X = apply_transforms(X, transforms)

        param_grid = None
        if algorithm == 'logistic':
            param_grid = [{'penalty': ['l1', 'l2'], 'C': [0.1, 0.3, 1.0, 3.0]}]
        elif algorithm == 'ridge':
            param_grid = [{'alpha': [0.1, 0.3, 1.0, 3.0, 10.0]}]
        elif algorithm == 'svm':
            param_grid = [{'C': [1, 10, 100, 1000], 'kernel': ['linear']},
                          {'C': [1, 10, 100, 1000], 'gamma': [0.001, 0.0001], 'kernel': ['rbf']}]
        elif algorithm == 'sgd':
            param_grid = [{'loss': ['hinge', 'log', 'modified_huber'], 'penalty': ['l1', 'l2'],
                           'alpha': [0.0001, 0.001, 0.01], 'iter': [100, 1000, 10000]}]
        elif algorithm == 'forest' or algorithm == 'xt':
            param_grid = [{'n_estimators': [10, 30, 100, 300], 'criterion': ['gini', 'entropy', 'mse'],
                           'max_features': ['auto', 'log2', None], 'max_depth': [3, 5, 7, 9, None],
                           'min_samples_split': [2, 10, 30, 100], 'min_samples_leaf': [1, 3, 10, 30, 100]}]
        elif algorithm == 'boost':
            param_grid = [{'learning_rate': [0.1, 0.3, 1.0], 'subsample': [1.0, 0.9, 0.7, 0.5],
                           'n_estimators': [100, 300, 1000], 'max_features': ['auto', 'log2', None],
                           'max_depth': [3, 5, 7, 9, None], 'min_samples_split': [2, 10, 30, 100],
                           'min_samples_leaf': [1, 3, 10, 30, 100]}]

        t0 = time.time()
        grid_estimator = GridSearchCV(model, param_grid, scoring=metric, cv=n_folds, n_jobs=1)
        grid_estimator.fit(X, y)
        t1 = time.time()
        print('Grid search completed in {0:3f} s.'.format(t1 - t0))

        print('Best params ='), grid_estimator.best_params_
        print('Best score ='), grid_estimator.best_score_


def xbg_parameter_search(X, y, metric):
    """
    Performs an exhaustive search over the specified model parameters.
    """
    categories = []
    # categories = [3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 16, 19, 21, 27, 28, 29]
    # categories = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18,
    #               19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    transforms = [OneHotEncoder(n_values='auto', categorical_features=categories, sparse=False),
                  StandardScaler()]

    X_train, X_eval, y_train, y_eval = train_test_split(X, y, test_size=0.1)
    transforms = fit_transforms(X_train, y_train, transforms)
    X_train = apply_transforms(X_train, transforms)
    X_eval = apply_transforms(X_eval, transforms)

    for subsample in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]:
        for colsample_bytree in [1.0, 0.9, 0.8, 0.7]:
            for max_depth in [3, 5, 7, 9]:
                for min_child_weight in [1, 3, 5, 7]:
                    t0 = time.time()
                    model = XGBRegressor(max_depth=max_depth, learning_rate=0.005, n_estimators=5000, silent=True,
                                         objective='reg:linear', gamma=0, min_child_weight=min_child_weight,
                                         max_delta_step=0, subsample=subsample, colsample_bytree=colsample_bytree,
                                         base_score=0.5, seed=0, missing=None)

                    print('subsample ='), subsample
                    print('colsample_bytree ='), colsample_bytree
                    print('max_depth ='), max_depth
                    print('min_child_weight ='), min_child_weight

                    print('Model hyper-parameters:')
                    print(model.get_params())

                    print('Fitting model...')
                    model.fit(X_train, y_train, eval_set=[(X_eval, y_eval)], eval_metric='rmse',
                              early_stopping_rounds=100, verbose=False)
                    print('Best iteration ='), model.best_iteration

                    train_score = predict_score(X_train, y_train, model, metric)
                    print('Training score ='), train_score

                    eval_score = predict_score(X_eval, y_eval, model, metric)
                    print('Evaluation score ='), eval_score

                    t1 = time.time()
                    print('Model trained in {0:3f} s.'.format(t1 - t0))
                    print('')
                    print('')


def nn_parameter_search(X, y, metric):
    """
    Performs an exhaustive search over the specified model parameters.
    """
    categories = [3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 16, 19, 21, 27, 28, 29]
    transforms = [FactorToNumeric(categorical_features=categories, metric='mean'),
                  StandardScaler()]

    X_train, X_eval, y_train, y_eval = train_test_split(X, y, test_size=0.1)
    transforms = fit_transforms(X_train, y_train, transforms)
    X_train = apply_transforms(X_train, transforms)
    X_eval = apply_transforms(X_eval, transforms)

    # init_methods = ['glorot_normal', 'glorot_uniform', 'he_normal', 'he_uniform']
    # optimization_methods = ['adagrad', 'adadelta', 'rmsprop', 'adam']
    # layer_sizes = [64, 128, 256, 384, 512]
    # hidden_layers = [1, 2, 3, 4]
    # batch_sizes = [16, 32, 64, 128]

    # init_methods = ['glorot_uniform']
    # optimization_methods = ['adadelta', 'rmsprop']
    # layer_sizes = [64, 128, 192]
    # hidden_layers = [1, 2, 3, 4]
    # batch_sizes = [128]

    init_methods = ['glorot_uniform']
    optimization_methods = ['adadelta']
    layer_sizes = [64, 128, 256]
    hidden_layers = [1, 2, 3, 4]
    batch_sizes = [128]

    for init_method in init_methods:
        for optimization_method in optimization_methods:
            for layer_size in layer_sizes:
                for hidden_layer in hidden_layers:
                    for batch_size in batch_sizes:
                        t0 = time.time()
                        print('Compiling model...')
                        model = define_nn_model_detailed(input_size=X_train.shape[1],
                                                         layer_size=layer_size,
                                                         output_size=1,
                                                         n_hidden_layers=hidden_layer,
                                                         init_method=init_method,
                                                         loss_function='mse',
                                                         input_activation='prelu',
                                                         hidden_activation='prelu',
                                                         output_activation='linear',
                                                         use_batch_normalization=True,
                                                         input_dropout=0.5,
                                                         hidden_dropout=0.5,
                                                         optimization_method=optimization_method)

                        print('init_method ='), init_method
                        print('optimization_method ='), optimization_method
                        print('layer_size ='), layer_size
                        print('hidden_layer ='), hidden_layer
                        print('batch_size ='), batch_size

                        print('Model hyper-parameters:')
                        print(model.get_config())

                        print('Fitting model...')
                        # eval_monitor = EarlyStopping(monitor='val_loss', patience=100, verbose=0)
                        # history = model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=1000, verbose=0,
                        #                     validation_data=(X_eval, y_eval), shuffle=True, callbacks=[eval_monitor])
                        history = model.fit(X_train, y_train, batch_size=batch_size, nb_epoch=1000, verbose=0,
                                            validation_data=(X_eval, y_eval), shuffle=True)
                        print('Min eval loss ='), min(history.history['val_loss'])
                        print('Min eval epoch ='), min(enumerate(history.history['loss']), key=lambda x: x[1])[0] + 1

                        train_score = predict_score(X_train, y_train, model, metric)
                        print('Training score ='), train_score

                        eval_score = predict_score(X_eval, y_eval, model, metric)
                        print('Evaluation score ='), eval_score

                        t1 = time.time()
                        print('Model trained in {0:3f} s.'.format(t1 - t0))
                        print('')
                        print('')


def bag_of_models(input_size):
    """
    Defines the set of models used in the ensemble.
    """
    models = []
    rf1 = RandomForestRegressor(n_estimators=100, criterion='mse', max_features='auto', max_depth=12,
                                min_samples_split=20, min_samples_leaf=10, max_leaf_nodes=None, n_jobs=-1)
    models.append(BaggingRegressor(base_estimator=rf1, n_estimators=10, max_samples=1.0, max_features=1.0,
                                   bootstrap=True, bootstrap_features=False))

    xg1 = XGBRegressor(max_depth=5, learning_rate=0.005, n_estimators=2000, silent=True,
                       objective='reg:linear', gamma=0, min_child_weight=1, max_delta_step=0,
                       subsample=1.0, colsample_bytree=1.0, base_score=0.5, seed=0, missing=None)
    models.append(BaggingRegressor(base_estimator=xg1, n_estimators=10, max_samples=1.0, max_features=1.0,
                                   bootstrap=True, bootstrap_features=False))

    xg2 = XGBRegressor(max_depth=7, learning_rate=0.005, n_estimators=1800, silent=True,
                       objective='reg:linear', gamma=0, min_child_weight=1, max_delta_step=0,
                       subsample=0.9, colsample_bytree=0.8, base_score=0.5, seed=0, missing=None)
    models.append(BaggingRegressor(base_estimator=xg2, n_estimators=10, max_samples=1.0, max_features=1.0,
                                   bootstrap=True, bootstrap_features=False))

    nn1 = define_nn_model_detailed(input_size=input_size,
                                   layer_size=64,
                                   output_size=1,
                                   n_hidden_layers=1,
                                   init_method='glorot_uniform',
                                   loss_function='mse',
                                   input_activation='prelu',
                                   hidden_activation='prelu',
                                   output_activation='linear',
                                   use_batch_normalization=True,
                                   input_dropout=0.5,
                                   hidden_dropout=0.5,
                                   optimization_method='adadelta')
    models.append(nn1)

    nn2 = define_nn_model_detailed(input_size=input_size,
                                   layer_size=128,
                                   output_size=1,
                                   n_hidden_layers=3,
                                   init_method='glorot_uniform',
                                   loss_function='mse',
                                   input_activation='prelu',
                                   hidden_activation='prelu',
                                   output_activation='linear',
                                   use_batch_normalization=True,
                                   input_dropout=0.5,
                                   hidden_dropout=0.75,
                                   optimization_method='adadelta')
    models.append(nn2)

    return models


def train_averaged_ensemble(X, y, X_test, metric, transforms, n_folds):
    """
    Creates an averaged ensemble of many models together.
    """
    t0 = time.time()
    models = bag_of_models(X.shape[1])
    n_models = len(models)
    n_records = y.shape[0]

    model_train_scores = np.zeros((n_folds, n_models))
    y_models = np.zeros((n_records, n_models))
    y_avg = np.zeros(n_records)
    y_true = np.zeros(n_records)

    folds = list(KFold(n_records, n_folds=n_folds, shuffle=True, random_state=1337))
    for i, (train_index, eval_index) in enumerate(folds):
        print('Starting fold {0}...'.format(i + 1))
        X_train = X[train_index]
        y_train = y[train_index]
        X_eval = X[eval_index]
        y_eval = y[eval_index]

        transforms = fit_transforms(X_train, y_train, transforms)
        X_train = apply_transforms(X_train, transforms)
        X_eval = apply_transforms(X_eval, transforms)

        print('Fitting individual models...')
        for k, model in enumerate(models):
            model.fit(X_train, y_train)

        print('Generating predictions and scoring...')
        for k, model in enumerate(models):
            model_train_scores[i, k] = score(y_train, model.predict(X_train), metric)
            y_models[eval_index, k] = model.predict(X_eval)

        y_avg[eval_index] = y_models[eval_index, :].sum(axis=1) / n_models
        y_true[eval_index] = y_eval

    t1 = time.time()
    print('Ensemble training completed in {0:3f} s.'.format(t1 - t0))

    for k, model in enumerate(models):
        print('Model ' + str(k) + ' average training score ='), model_train_scores[:, k].sum(axis=0) / n_folds
        print('Model ' + str(k) + ' eval score ='), score(y_true, y_models[:, k], metric)
    print('Ensemble eval score ='), score(y_true, y_avg, metric)

    df = pd.DataFrame(y_models, columns=['Model ' + str(i) for i in range(n_models)])
    visualize_correlations(df)

    print('Fitting models on full data set...')
    n_test_records = X_test.shape[0]
    y_models_test = np.zeros((n_test_records, n_models))

    transforms = fit_transforms(X, y, transforms)
    X = apply_transforms(X, transforms)
    X_test = apply_transforms(X_test, transforms)

    for k, model in enumerate(models):
        model.fit(X, y)

    print('Generating test data predictions...')
    for k, model in enumerate(models):
        y_models_test[:, k] = model.predict(X_test)

    y_avg_test = y_models_test.sum(axis=1) / n_models

    print('Ensemble complete.')
    return y_avg_test


def train_stacked_ensemble(X, y, X_test, metric, transforms, n_folds):
    """
    Creates a stacked ensemble of many models together.
    """
    t0 = time.time()
    models = bag_of_models(X.shape[1])
    stacker = Ridge()
    n_models = len(models)
    n_records = y.shape[0]

    model_train_scores = np.zeros((n_folds, n_models))
    stacker_train_scores = np.zeros(n_folds)
    y_models = np.zeros((n_records, n_models))
    y_pred = np.zeros(n_records)
    y_true = np.zeros(n_records)

    folds = list(KFold(n_records, n_folds=n_folds, shuffle=True, random_state=1337))
    for i, (train_out_index, eval_out_index) in enumerate(folds):
        print('Starting fold {0}...'.format(i + 1))
        X_out_train = X[train_out_index]
        y_out_train = y[train_out_index]
        X_out_eval = X[eval_out_index]
        y_out_eval = y[eval_out_index]

        y_oos = np.zeros((n_records, n_models))

        print('Generating out-of-sample predictions for first-level models...')
        for j, (train_index, eval_index) in enumerate(folds):
            if j != i:
                X_train = X[train_index]
                y_train = y[train_index]
                X_eval = X[eval_index]

                transforms = fit_transforms(X_train, y_train, transforms)
                X_train = apply_transforms(X_train, transforms)
                X_eval = apply_transforms(X_eval, transforms)

                for k, model in enumerate(models):
                    if k < 3:
                        model.fit(X_train, y_train)
                    elif k == 3:
                        model.fit(X_train, y_train, batch_size=128, nb_epoch=400, verbose=0, shuffle=True)
                    else:
                        model.fit(X_train, y_train, batch_size=128, nb_epoch=1000, verbose=0, shuffle=True)

                for k, model in enumerate(models):
                    y_oos[eval_index, k] = model.predict(X_eval).ravel()

        print('Fitting second-level model...')
        stacker.fit(y_oos[train_out_index], y_out_train)

        print('Re-fitting first-level models...')
        transforms = fit_transforms(X_out_train, y_out_train, transforms)
        X_out_train = apply_transforms(X_out_train, transforms)
        X_out_eval = apply_transforms(X_out_eval, transforms)

        for k, model in enumerate(models):
            if k < 3:
                model.fit(X_out_train, y_out_train)
            elif k == 3:
                model.fit(X_out_train, y_out_train, batch_size=128, nb_epoch=400, verbose=0, shuffle=True)
            else:
                model.fit(X_out_train, y_out_train, batch_size=128, nb_epoch=1000, verbose=0, shuffle=True)

        print('Generating predictions and scoring...')
        training_predictions = np.zeros((X_out_train.shape[0], n_models))

        for k, model in enumerate(models):
            training_predictions[:, k] = model.predict(X_out_train).ravel()
            model_train_scores[i, k] = score(y_out_train, training_predictions[:, k], metric)

        stacker_train_scores[i] = score(y_out_train, stacker.predict(training_predictions), metric)

        for k, model in enumerate(models):
            y_models[eval_out_index, k] = model.predict(X_out_eval).ravel()

        y_pred[eval_out_index] = stacker.predict(y_models[eval_out_index, :])
        y_true[eval_out_index] = y_out_eval

    t1 = time.time()
    print('Ensemble training completed in {0:3f} s.'.format(t1 - t0))

    for k, model in enumerate(models):
        print('Model ' + str(k) + ' average training score ='), model_train_scores[:, k].sum(axis=0) / n_folds
        print('Model ' + str(k) + ' eval score ='), score(y_true, y_models[:, k], metric)
    print('Ensemble average training score ='), stacker_train_scores.sum() / n_folds
    print('Ensemble eval score ='), score(y_true, y_pred, metric)

    df = pd.DataFrame(y_models, columns=['Model ' + str(i) for i in range(n_models)])
    visualize_correlations(df)

    print('Fitting models on full data set...')
    n_test_records = X_test.shape[0]
    y_models_test = np.zeros((n_test_records, n_models))

    transforms = fit_transforms(X, y, transforms)
    X = apply_transforms(X, transforms)
    X_test = apply_transforms(X_test, transforms)

    for k, model in enumerate(models):
        if k < 3:
            model.fit(X, y)
        elif k == 3:
            model.fit(X, y, batch_size=128, nb_epoch=400, verbose=0, shuffle=True)
        else:
            model.fit(X, y, batch_size=128, nb_epoch=1000, verbose=0, shuffle=True)

    stacker.fit(y_models, y_true)

    print('Generating test data predictions...')
    for k, model in enumerate(models):
        y_models_test[:, k] = model.predict(X_test).ravel()

    y_pred_test = stacker.predict(y_models_test)

    print('Ensemble complete.')
    return y_models, y_true, y_models_test, y_pred_test


def create_submission(test_data, y_pred, data_dir, submit_file):
    """
    Create a new submission file with test data and predictions generated by the model.
    """
    submit = pd.DataFrame(columns=['Id', 'Hazard'])
    submit['Id'] = test_data.index
    submit['Hazard'] = y_pred
    submit.to_csv(data_dir + submit_file, sep=',', index=False, index_label=False)
    print('Submission file complete.')


def experiments():
    """
    Testing area for miscellaneous experiments.
    """


def main():
    ex_process_train_data = True
    ex_generate_features = False
    ex_load_model = False
    ex_save_model = False
    ex_visualize_variable_relationships = False
    ex_visualize_feature_distributions = False
    ex_visualize_correlations = False
    ex_visualize_sequential_relationships = False
    ex_visualize_transforms = False
    ex_define_model = True
    ex_train_model = True
    ex_visualize_feature_importance = False
    ex_cross_validate = True
    ex_plot_learning_curve = False
    ex_parameter_search = False
    ex_train_ensemble = False
    ex_create_submission = True

    train_file = 'train.csv'
    test_file = 'test.csv'
    submit_file = 'submission.csv'
    model_file = 'model.pkl'

    model_type = 'regression'  # classification, regression
    algorithm = 'xgb'  # bayes, logistic, ridge, svm, sgd, forest, xt, boost, xgb, nn
    metric = 'gini'  # accuracy, f1, log_loss, mean_absolute_error, mean_squared_error, r2, roc_auc, 'gini'
    ensemble_mode = 'stacking'  # averaging, stacking
    # categories = []
    categories = [3, 4, 5, 6, 7, 8, 10, 11, 14, 15, 16, 19, 21, 27, 28, 29]
    # categories = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18,
    #               19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
    early_stopping = False
    label_index = 0
    column_offset = 1
    plot_size = 16
    n_components = 2
    n_folds = 5

    train_data = None
    test_data = None
    X = None
    y = None
    X_test = None
    y_pred = None
    model = None

    all_transforms = [Imputer(missing_values='NaN', strategy='mean', axis=0),
                      LabelEncoder(),
                      OneHotEncoder(n_values='auto', categorical_features=categories, sparse=False),
                      DictVectorizer(sparse=False),
                      FeatureHasher(n_features=1048576, input_type='dict'),
                      VarianceThreshold(threshold=0.0),
                      Binarizer(threshold=0.0),
                      StandardScaler(),
                      MinMaxScaler(),
                      PCA(n_components=None, whiten=False),
                      TruncatedSVD(n_components=None),
                      NMF(n_components=None),
                      FastICA(n_components=None, whiten=True),
                      Isomap(n_components=2),
                      LocallyLinearEmbedding(n_components=2, method='modified'),
                      MDS(n_components=2),
                      TSNE(n_components=2, learning_rate=1000, n_iter=1000),
                      KMeans(n_clusters=8)]

    transforms = [FactorToNumeric(categorical_features=categories, metric='mean'),
                  StandardScaler()]

    print('Starting process (' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ')...')
    print('Model Type = {0}'.format(model_type))
    print('Algorithm = {0}'.format(algorithm))
    print('Scoring Metric = {0}'.format(metric))
    print('Generate Features = {0}'.format(ex_generate_features))
    print('Transforms = {0}'.format(transforms))
    print('Early Stopping = {0}'.format(early_stopping))

    if ex_process_train_data:
        print('Reading in and processing data files...')
        train_data, test_data, X, y, X_test = process_data(data_dir, train_file, test_file, label_index,
                                                           column_offset, ex_generate_features)

    if ex_visualize_variable_relationships:
        print('Visualizing pairwise relationships...')
        # scatter, reg, resid, kde, hex
        visualize_variable_relationships(train_data, 'scatter', ['Hazard', 'T1_V1'])

    if ex_visualize_feature_distributions:
        print('Visualizing feature distributions...')
        # hist, kde
        visualize_feature_distributions(train_data, 'hist', plot_size)

    if ex_visualize_correlations:
        print('Visualizing feature correlations...')
        visualize_correlations(train_data)

    if ex_visualize_sequential_relationships:
        print('Visualizing sequential relationships...')
        visualize_sequential_relationships(train_data, plot_size)

    if ex_visualize_transforms:
        print('Visualizing transformed data...')
        visualize_transforms(X, y, model_type, n_components, transforms)

    if ex_load_model:
        print('Loading model from disk...')
        model = load_model(data_dir + model_file)
    
    if ex_define_model:
        print('Building model definition...')
        if algorithm == 'nn':
            model = define_nn_model(X, y, transforms)
        else:
            model = define_model(model_type, algorithm)

    if ex_train_model:
        print('Training model...')
        if algorithm == 'nn':
            model, history = train_model(X, y, algorithm, model, metric, transforms, early_stopping)
        else:
            model = train_model(X, y, algorithm, model, metric, transforms, early_stopping)

        if ex_visualize_feature_importance and algorithm in ['forest', 'xt', 'boost']:
            print('Generating feature importance plot...')
            visualize_feature_importance(train_data, model, column_offset)

        if ex_cross_validate:
            print('Performing cross-validation...')
            cross_validate(X, y, algorithm, model, metric, transforms, n_folds)

        if ex_plot_learning_curve:
            print('Generating learning curve...')
            plot_learning_curve(X, y, model, metric, transforms, n_folds)

    if ex_save_model:
        print('Saving model to disk...')
        save_model(model, data_dir + model_file)

    if ex_parameter_search:
        print('Performing hyper-parameter grid search...')
        parameter_search(X, y, algorithm, model, metric, transforms, n_folds)

    if ex_train_ensemble:
        print('Creating an ensemble of models...')
        if ensemble_mode == 'averaging':
            y_pred = train_averaged_ensemble(X, y, X_test, metric, transforms, n_folds)
        else:
            y_models, y_true, y_models_test, y_pred = train_stacked_ensemble(X, y, X_test, metric, transforms, n_folds)
            pd.DataFrame(y_models).to_csv(data_dir + 'stacker_train.csv')
            pd.DataFrame(y_true).to_csv(data_dir + 'stacker_label.csv')
            pd.DataFrame(y_models_test).to_csv(data_dir + 'stacker_test.csv')

    if ex_create_submission:
        if not ex_train_ensemble:
            print('Predicting test data...')
            transforms = fit_transforms(X, y, transforms)
            X_test = apply_transforms(X_test, transforms)
            y_pred = model.predict(X_test)

        print('Creating submission file...')
        create_submission(test_data, y_pred, data_dir, submit_file)

    print('Process complete. (' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ')')
    print('')
    print('')
    logger.flush()


if __name__ == "__main__":
    main()
