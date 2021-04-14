import pytest
import torch
from torch import nn
from torch.nn.utils import parameters_to_vector

from laplace.curvature import BackPackGGN
from laplace.jacobians import Jacobians


@pytest.fixture
def model():
    torch.manual_seed(711)
    model = torch.nn.Sequential(nn.Linear(3, 20), nn.Linear(20, 2))
    setattr(model, 'output_size', 2)
    model_params = list(model.parameters())
    setattr(model, 'n_layers', len(model_params))  # number of parameter groups
    setattr(model, 'n_params', len(parameters_to_vector(model_params)))
    return model


@pytest.fixture
def class_Xy():
    X = torch.randn(10, 3)
    y = torch.randint(2, (10,))
    return X, y


@pytest.fixture
def reg_Xy():
    X = torch.randn(10, 3)
    y = torch.randn(10, 2)
    return X, y


def test_full_ggn_backpack_reg_integration(reg_Xy, model):
    X, y = reg_Xy
    backend = BackPackGGN(model, 'regression', stochastic=True)
    with pytest.raises(ValueError):
        loss, fggn = backend.full(X, y)

    # cannot test, its implemented based on Jacobians.
    backend = BackPackGGN(model, 'regression', stochastic=False)
    loss, H_ggn = backend.full(X, y)
    assert H_ggn.size() == torch.Size((model.n_params, model.n_params))
    

def test_full_ggn_backpack_cls_integration(class_Xy, model):
    X, y = class_Xy
    backend = BackPackGGN(model, 'classification', stochastic=True)
    with pytest.raises(ValueError):
        loss, fggn = backend.full(X, y)

    # cannot test, its implemented based on Jacobians.
    backend = BackPackGGN(model, 'classification', stochastic=False)
    loss, H_ggn = backend.full(X, y)
    assert H_ggn.size() == torch.Size((model.n_params, model.n_params))
    

def test_diag_ggn_cls_backpack(class_Xy, model):
    X, y = class_Xy
    backend = BackPackGGN(model, 'classification', stochastic=False)
    loss, dggn = backend.diag(X, y)
    # sanity check size of diag ggn
    assert len(dggn) == model.n_params

    # check against manually computed full GGN:
    backend = BackPackGGN(model, 'classification', stochastic=False)
    loss_f, H_ggn = backend.full(X, y)
    assert loss == loss_f
    assert torch.allclose(dggn, H_ggn.diagonal())


def test_diag_ggn_reg_backpack(reg_Xy, model):
    X, y = reg_Xy
    backend = BackPackGGN(model, 'regression', stochastic=False)
    loss, dggn = backend.diag(X, y)
    # sanity check size of diag ggn
    assert len(dggn) == model.n_params

    # check against manually computed full GGN:
    backend = BackPackGGN(model, 'regression', stochastic=False)
    loss_f, H_ggn = backend.full(X, y)
    assert loss == loss_f
    assert torch.allclose(dggn, H_ggn.diagonal())


def test_diag_ggn_stoch_cls_backpack(class_Xy, model):
    X, y = class_Xy
    backend = BackPackGGN(model, 'classification', stochastic=True)
    loss, dggn = backend.diag(X, y)
    # sanity check size of diag ggn
    assert len(dggn) == model.n_params

    # same order of magnitude os non-stochastic.
    backend = BackPackGGN(model, 'classification', stochastic=False)
    loss_ns, dggn_ns = backend.diag(X, y)
    assert loss_ns == loss
    assert torch.allclose(dggn, dggn_ns, atol=1e-8, rtol=1e1)


def test_diag_ggn_stoch_reg_backpack(reg_Xy, model):
    X, y = reg_Xy
    backend = BackPackGGN(model, 'regression', stochastic=True)
    loss, dggn = backend.diag(X, y)
    # sanity check size of diag ggn
    assert len(dggn) == model.n_params

    # same order of magnitude os non-stochastic.
    backend = BackPackGGN(model, 'regression', stochastic=False)
    loss_ns, dggn_ns = backend.diag(X, y)
    assert loss_ns == loss
    assert torch.allclose(dggn, dggn_ns, atol=1e-8, rtol=1e1)