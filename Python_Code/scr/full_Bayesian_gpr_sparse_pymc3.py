import pymc3 as pm
import numpy as np
import matplotlib.pyplot as plt
from timeit import default_timer as timer

"""
This code executes the training and prediction of standard GPR going full bayesian and print its properties  
"""

def full_bayesian_gpr_sparse_pymc3_ex(amountTraining, amount_Inducing, amountTest, trainingValues, trainingParameters, testValues, testParameters):


    valuesFFTCallsTraining = np.squeeze(np.asarray(trainingValues))
    X = np.array(np.asarray(trainingParameters),dtype=np.float64)

    valuesFFTCallsTest = np.squeeze(np.asarray(testValues))
    X_new = np.array(np.asarray(testParameters),dtype=np.float64)

    dimension = X.shape[1]


    startFittingTimer = timer()
    with pm.Model() as model2:
        # Set priors on the hyperparameters of the covariance
        ls1 = pm.Gamma("lengthscale", alpha=2, beta=2)

        eta = pm.HalfNormal("signal variance", sigma=2)

        #ls1 = pm.Normal("ls1", 2, 2)
        #eta = pm.Normal("eta", 1,sigma=2)

        cov = eta ** 2 * pm.gp.cov.ExpQuad(dimension, ls1)  # cov_x1 must accept X1 without error

        # Specify the GP.  The default mean function is `Zero`.
        gp = pm.gp.MarginalSparse(cov_func=cov, approx="VFE")

        Xu = pm.gp.util.kmeans_inducing_points(amount_Inducing, X)
        sigma = pm.HalfNormal("sigma", sigma=0.01)         #halfnormal always positive

        # Place a GP prior over the function f.
        gp.marginal_likelihood("y", X=X, Xu=Xu, y=valuesFFTCallsTraining, noise=sigma)

    with model2:
        #trace = pm.sample(draws = 500,tune=500, step=pm.Metropolis(), cores=1)
        trace = pm.sample(draws=500, tune=500, cores=1)

    endFittingTimer = timer()
    print('Timer of fitting in sample ' + str(endFittingTimer - startFittingTimer))

    pm.traceplot(trace)
    plt.show()

    startPredictingInSampleTimerGPR = timer()
    with model2:
        f_pred = gp.conditional("f_pred", X)

    with model2:
        pred_samples = pm.sample_posterior_predictive(trace, vars=[f_pred])

    mu =np.mean(pred_samples["f_pred"], axis=0)
    endPredictingInSampleTimerGPR = timer()
    mu = np.maximum(mu, 0)

    AEE = np.sum(np.abs((valuesFFTCallsTraining - mu)))/amountTraining
    MAE = np.max(np.abs((valuesFFTCallsTraining - mu)))
    print('Timer of predicting in sample with GPR ' + str(
        endPredictingInSampleTimerGPR - startPredictingInSampleTimerGPR))

    print('In sample MAE ' + str(MAE))
    print('In sample AEE ' + str(AEE))

    startPredictingOutSampleTimerGPR = timer()
    with model2:
        f_pred_new = gp.conditional("f_pred_new", X_new)

    with model2:
        pred_samples_new = pm.sample_posterior_predictive(trace, vars=[f_pred_new])

    mu =np.mean(pred_samples_new["f_pred_new"], axis=0)
    endPredictingOutSampleTimerGPR = timer()
    print('Timer of predicting out sample GPR ' + str(endPredictingOutSampleTimerGPR - startPredictingOutSampleTimerGPR))

    mu = np.maximum(mu, 0)

    AEE = np.sum(np.abs((valuesFFTCallsTest - mu)))/amountTest
    MAE = np.max(np.abs((valuesFFTCallsTest - mu)))

    print('In sample MAE ' + str(MAE))
    print('In sample AEE ' + str(AEE))

    # fig = plt.figure(figsize=(12, 5));
    # ax = fig.gca()
    #
    # #plot the samples from the gp posterior with samples and shading
    # from pymc3.gp.util import plot_gp_dist
    # plot_gp_dist(ax, pred_samples["f_pred"], X[:,5]);
    #
    # # plot the data and the true latent function
    # ax.set_title('Vanilla Call Option Regression')
    # ax.set_xlabel('Strike')
    # ax.set_ylabel('Price')
    # plt.plot(X[:,5], trainingValues.transpose(), 'ok', ms=3, alpha=0.5, label="Observed data");
    # #plt.plot(Xu[:, 5], 1, 'ok', ms=3, alpha=0.5, label="Observed data");
    # plt.xticks(Xu[:, 5])
    # plt.show()