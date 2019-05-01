import os
import itertools

import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.svm import SVC
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import GridSearchCV

LEGEND_COORDS = (1.2, 0.8)
TOTAL_PCA_COMPONENTS = 60
CLASS_MAP = {5: 'eyes open', 4: 'eyes closed', 3: 'healthy brain area',
             2: 'tumor area', 1: 'seizure activity'}


def main():
    """Explore epileptic seizure classification data set

    Returns:
        None
    """
    epidata = pd.read_csv(os.path.join('data', 'data.csv'))
    set_matplotlib_params()
    # explore_data(epidata)
    features = epidata.drop(['y', 'Unnamed: 0'], axis=1)
    target = epidata['y']
    x_train, x_test, y_train, y_test = train_test_split(features, target,
                                                        test_size=0.3,
                                                        random_state=0)
    explore_pca(x_train, y_train)
    naive = get_naive_features(x_train)
    make_feature_scatter_plots(naive, y_train)
    make_violin_plots(naive, y_train)
    test_pca_svm(x_train, (y_train == 1).astype(int), x_test,
                 (y_test == 1).astype(int))


def test_pca_svm(x_train, y_train, x_test, y_test):
    """Train and test a PCA and SVM classifier

    Train a pipeline with principal components analysis dimensionality
    reduction followed by a support vector machine (SVM) with a radial basis
    function kernel. Optimize the parameters of the SVM and train with the
    training set. Run on the test set and save the classification report as
    a csv file.

    Args:
        x_train: pandas DataFrame
            Features for training
        y_train: pandas Series
            Targets for training
        x_test: pandas DataFrame
            Features for testing
        y_test:
            Targets for testing

    Returns:
        None
    """
    pca = PCA(n_components=25, svd_solver='randomized',
              whiten=True).fit(x_train)
    x_train_pca = pca.transform(x_train)
    x_test_pca = pca.transform(x_test)
    param_grid = {'C': [1e3, 5e3, 1e4, 5e4, 1e5],
                  'gamma': [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.1], }
    clf = GridSearchCV(SVC(kernel='rbf', class_weight='balanced'),
                       param_grid, cv=5)
    clf = clf.fit(x_train_pca, y_train)
    y_pred = clf.predict(x_test_pca)
    write_class_report_file(y_test, y_pred,
                            os.path.join('outputs', 'best_svm.csv'))


def write_class_report_file(true, pred, filename):
    """Write a classification report to a csv file

    Args:
        true: sequence
            True classification labels
        pred: sequence of same size as true
            Predicted classification labels
        filename: str
            Path to which to save comma-separated value file with
            classification report

    Returns:
        None
    """
    clf_rep = precision_recall_fscore_support(true, pred)
    out_dict = {"precision": clf_rep[0].round(2),
                "recall": clf_rep[1].round(2),
                "f1-score": clf_rep[2].round(2),
                "support": clf_rep[3]}
    out_df = pd.DataFrame(out_dict)
    avg_tot = (out_df.apply(lambda x: round(x.mean(), 2) if x.name != "support"
               else round(x.sum(), 2)).to_frame().T)
    avg_tot.index = ["avg/total"]
    out_df = out_df.append(avg_tot)
    out_df.to_csv(filename)


def make_violin_plots(features, targets):
    """Make seaborn violin plots of the features, grouped by target value

    For each feature, group the data points by target value. Create a seaborn
    violin plot showing approximate distributions for the feature in each
    target group. Label the plot and save it with a name that references the
    feature.

    Args:
        features: pandas DataFrame
            Feature values. Each row is a data point and each column is a
            feature.
        targets: pandas Series
            Class for each data point. Must have the same number of rows as the
            features argument.

    Returns:
        None
    """
    features['y'] = targets.map(CLASS_MAP)
    for col in features.columns:
        if col is not 'y':
            plot_axes = sns.violinplot(x=col, y='y', data=features)
            fig = plot_axes.get_figure()
            filename = os.path.join('outputs', col + '_violin.png')
            fig.savefig(filename, bbox_inches='tight')
            fig.clf()


def make_feature_scatter_plots(features, targets):
    """Create scatter plots of all 2-combinations of features

    The scatter plots colour the points by class. They are saved to png
    files with the names of the two plotted features.

    Args:
        features: pandas DataFrame
            Features to plot. Rows are data points and columns are features.
        targets: pandas Series
            Classification of each data point. Must have the same number of rows
            as the features argument.

    Returns:
        None
    """
    for (xvar, yvar) in itertools.combinations(features.columns, 2):
        plot_axes = plt.subplot(1, 1, 1)
        for class_num in sorted(targets.unique()):
            to_plot = targets == class_num
            xvals = features[xvar][to_plot]
            yvals = features[yvar][to_plot]
            plot_axes.scatter(xvals, yvals, label=CLASS_MAP[class_num], s=1)
        plot_axes.set_xlabel(xvar)
        plot_axes.set_ylabel(yvar)
        plot_axes.legend(loc='right', bbox_to_anchor=(1.4, 0.8))
        fig = plot_axes.get_figure()
        filename = os.path.join('outputs', xvar + '_vs_' + yvar + '.png')
        fig.savefig(filename, bbox_inches='tight')
        fig.clf()


def get_naive_features(data):
    """Calculate the mean, min, max, std, quartiles, and range of the data

    Args:
        data: pandas DataFrame
            data to calculate statistics of. Each data point is a row.

    Returns: pandas DataFrame
        Columns are 'min', 'max', 'range', 'mean', '25%', '50%', and '75%'
    """
    result = data.transpose().describe().transpose()
    result = result.drop('count', axis=1)
    result['range'] = result['max'] - result['min']
    return result


def explore_pca(x_train, y_train, n_components=TOTAL_PCA_COMPONENTS):
    """Create plots of Principal Component Analysis decomposition

    Find the first TOTAL_PCA_COMPONENTS PCA components of the argument. Create
    a plot of the explained variance ratio and a plot of the cumulative sum of
    the explained variance ratio, over the number of PCA components used. Save
    the explained variance ratio to a comma-separated file. Create a scatter
    plot of the data points versus the first two principal components, coloured
    by classification target. Create a line plot of the first five principal
    components.

    Args:
        x_train: pandas.DataFrame
            Training data to decompose using Principal Component Analysis
        y_train: pandas.Series
            Classification targets
        n_components : int, Optional, default 60
            Number of PCA components to use in plots and csv file

    Returns:
        None
    """
    pca = PCA(n_components=n_components)
    transformed = pca.fit_transform(x_train)
    components = pca.components_
    var_ratio = pd.Series(pca.explained_variance_ratio_)
    sum_var_ratio = var_ratio.cumsum()
    var_ratio.to_csv(os.path.join('outputs', 'var_ratio.csv'), header=True)
    plot_explained_variance(var_ratio, os.path.join('outputs', 'var_ratio.png'))
    plot_sum_explained_variance(sum_var_ratio,
                                os.path.join('outputs', 'var_ratio_sum.png'))
    first_two_pca_scatter(transformed[:, :2], y_train,
                          os.path.join('outputs', 'two_pca_components.png'))
    plot_components(components[:, :5], os.path.join('outputs',
                                                    'pca_components.png'))


def plot_components(components, filename):
    """Plot PCA components

    Args:
        components: pandas DataFrame or numpy ndarray
            Each component is a row and each column is one of the original
            features
        filename: str
            Path to file to which to save the figure. File format is inferred
            from the extension

    Returns:
        None
    """
    plot_axes = plt.subplot(1, 1, 1)
    plot_axes.plot(components)
    plot_axes.set_xlabel('Feature')
    plot_axes.set_ylabel('Component values')
    fig = plot_axes.get_figure()
    fig.savefig(filename, bbox_inches='tight')
    fig.clf()


def first_two_pca_scatter(components, targets, filename):
    """Make scatter plot of data vs 1st 2 PCA components, colored by target

    Args:
        components: numpy ndarray
            Principal Component Analysis components. Each row is a data point
            and each column is the value of that PCA component for that
            data point.
        targets: numpy ndarray or pandas Series
            Labels for each data point. Must have the same number of rows as
            the components argument
        filename: str
            Path to file to which to save the figure. File format is inferred
            from the extension

    Returns:
        None
    """
    plot_axes = plt.subplot(1, 1, 1)
    for class_num in sorted(targets.unique()):
        to_plot = targets == class_num
        plot_axes.scatter(components[to_plot, 0], components[to_plot, 1],
                          label=CLASS_MAP[class_num], s=1)
    plot_axes.set_xlabel('PCA component 1')
    plot_axes.set_ylabel('PCA component 2')
    plot_axes.legend(loc='right', bbox_to_anchor=(1.4, 0.8))
    fig = plot_axes.get_figure()
    fig.savefig(filename, bbox_inches='tight')
    fig.clf()


def plot_sum_explained_variance(var_ratio, filename):
    """Plot one minus cumulative sum of the explained variance of a transform

    Create a plot with a linear x-axis and a logarithmic y-axis of one minus
    the cumulative explained variance of the components of a dimensionality
    reduction method and save the plot to a file. This plot allows the user
    to determine how many components are required to achieve a certain total
    explained variance ratio, such as 90% or 99%.

    Args:
        var_ratio: pandas.Series
            Explained variance ratio of each component. Should be
            monotonically decreasing.
        filename: str
            Path to file to which to save the figure. File format is inferred
            from the extension
    Returns:
        None
    """
    plot_axes = plt.subplot(1, 1, 1)
    plot_axes.semilogy(1 - var_ratio, marker='.', linestyle='none')
    plot_axes.set_xlabel('PCA component')
    plot_axes.set_ylabel('1 - sum(Explained variance ratio)')
    fig = plot_axes.get_figure()
    fig.savefig(filename)
    fig.clf()


def plot_explained_variance(var_ratio, filename):
    """Plot the explained variance of each component of a transform

    Create a plot with a linear x-axis and a logarithmic y-axis of the
    explained variance ratio of each component. This plot allows the user
    to see how rapidly the explained variance decreases by component and to
    identify and eigengap, if it exists.

    Args:
        var_ratio: pandas.Series
            Explained variance ratio of each component. Should be
            monotonically decreasing.
        filename: str
            Path to file to which to save the figure. File format is inferred
            from the extension

    Returns:
        None
    """
    plot_axes = plt.subplot(1, 1, 1)
    plot_axes.semilogy(var_ratio, marker='.', linestyle='none')
    plot_axes.set_xlabel('PCA component')
    plot_axes.set_ylabel('Explained variance ratio')
    fig = plot_axes.get_figure()
    fig.savefig(filename)
    fig.clf()


def explore_data(epidata):
    """Create a number of plots and csv files to explore the seizure data

    Args:
        epidata: pandas.DataFrame
            Data about seizures. Each row is a data point and each column is
            a feature, except for the column 'y' which contains the
            classification target.
    Returns:
        None
    """
    features = epidata.drop(['y', 'Unnamed: 0'], axis=1)
    desc = features.describe()
    desc.transpose().describe().to_csv(os.path.join('outputs',
                                                    'double_desc.csv'))
    epidata['y'].value_counts().to_csv(os.path.join('outputs',
                                                    'class_counts.csv'),
                                       header=True)
    create_summary_plot(desc, os.path.join('outputs', 'feature_summary.png'))
    create_interquartile_plot(desc, os.path.join('outputs',
                                                 'interquartile.png'))
    create_mean_median_plot(desc, os.path.join('outputs', 'mean_median.png'))
    create_std_plot(desc.loc['std', :], os.path.join('outputs',
                                                     'feature_std.png'))
    create_corr_heatmap(features, os.path.join('outputs', 'corr_heatmap.png'),
                        os.path.join('outputs', 'corr_X90.png'))


def create_corr_heatmap(features, filename1, filename2):
    """Create 2 plots: a feature correlation heat map and correlations with X90

    Args:
        features: pandas.DataFrame
            Feature columns. Each row is a data point and each column is a
            feature. One column must be named 'X90'.
        filename1: str
            Path to which to save correlation heatmap figure. File format is
            inferred from the extension.
        filename2:
            Path to which to save figure showing correlations with feature X90.
            File format is inferred from the extension.

    Returns:
        None
    """
    corr_mat = features.corr()
    corr_mat.to_csv(os.path.join('outputs', 'corr_mat.csv'))
    plot_axes = corr_mat['X90'].plot()
    plot_axes.set_xlabel('Feature')
    plot_axes.set_ylabel('Correlation with feature X90')
    fig = plot_axes.get_figure()
    fig.savefig(filename2)
    fig.clf()
    sns.heatmap(corr_mat, center=0, cmap='coolwarm')
    fig.savefig(filename1)
    fig.clf()


def create_std_plot(std, filename):
    """Create plot of standard deviation of each feature

    Args:
        std: pandas.Series
            Standard deviation of each feature across the data set. The index is
            the name of the feature.
        filename: str
            Path to which to save the figure. The file format is inferred
            from the extension.

    Returns:
        None
    """
    plot_axes = std.plot()
    plot_axes.set_xlabel('Feature')
    plot_axes.set_ylabel('Standard deviation of feature value')
    fig = plot_axes.get_figure()
    fig.savefig(filename)
    fig.clf()


def create_summary_plot(description, filename):
    """Create a plot showing mean, min, max, and quartiles of features

    Args:
        description: pandas.DataFrame
            Description of the features. Result of running the
            pandas.DataFrame.describe method on the features
        filename: str
            Path to which to save the figure. The file format is inferred
            from the extension.

    Returns:
        None
    """
    to_plot = description.drop(['count', 'std']).transpose()
    create_feature_value_plot(to_plot, filename)


def create_interquartile_plot(data, filename):
    """Create a plot of the mean, median, and 25th and 75th percentile

    Args:
        data:  pandas.DataFrame
            Description of the features. Result of running the
            pandas.DataFrame.describe method on the features
        filename: str
            Path to which to save the figure. The file format is inferred
            from the extension.

    Returns:
        None
    """
    cols = ['mean', '25%', '50%', '75%']
    to_plot = data.transpose()[cols]
    create_feature_value_plot(to_plot, filename)


def create_mean_median_plot(data, filename):
    """Create a plot of the mean and median of the features

        Args:
            data:  pandas.DataFrame
                Description of the features. Result of running the
                pandas.DataFrame.describe method on the features
            filename: str
                Path to which to save the figure. The file format is inferred
                from the extension.

        Returns:
            None
        """
    cols = ['mean', '50%']
    to_plot = data.transpose()[cols]
    to_plot.columns = ['mean', 'median']
    create_feature_value_plot(to_plot, filename)


def create_feature_value_plot(data, filename):
    """Create a plot with features on the x-axis and values on the y-axis

        Args:
            data:  pandas.DataFrame
                Data to plot
            filename: str
                Path to which to save the figure. The file format is inferred
                from the extension.

        Returns:
            None
        """
    plot_axes = data.plot()
    plot_axes.set_xlabel('Feature')
    plot_axes.set_ylabel('Value')
    plot_axes.legend(loc='right', bbox_to_anchor=LEGEND_COORDS)
    fig = plot_axes.get_figure()
    fig.savefig(filename, bbox_inches='tight')
    fig.clf()


def set_matplotlib_params():
    """Set matplotlib parameters to chosen aesthetics

    Set the figure dots per inch to 200, and the edge, tick and axis label
    colors to gray for all future matplotlib calls.

    Returns:
        None
    """
    matplotlib.rcParams['savefig.dpi'] = 200
    matplotlib.rcParams['axes.edgecolor'] = 'gray'
    matplotlib.rcParams['xtick.color'] = 'gray'
    matplotlib.rcParams['ytick.color'] = 'gray'
    matplotlib.rcParams['axes.labelcolor'] = 'gray'


if __name__ == '__main__':
    main()
