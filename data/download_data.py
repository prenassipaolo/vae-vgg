import torchvision.transforms as transforms
import torchvision.datasets as datasets


def transform_data(size, padding, normalize_means : tuple, normalize_stds : tuple):
        # create transform function
    transform_train = transforms.Compose([
        transforms.RandomCrop(size=size, padding=padding),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(normalize_means, normalize_stds),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(normalize_means, normalize_stds),
    ])

    return transform_train, transform_test


# download CIFAR
def download_cifar_dataset():
    
    # create transform functions
    transform_train = transforms.Compose([
        transforms.RandomCrop(size=32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])

    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
    ])

    # create datasets
    train_data = datasets.CIFAR10(
        root="./data",
        train=True,
        download=True,
        transform=transform_train,
    )
    test_data = datasets.CIFAR10(
        root="./data",
        train=False,
        download=True,
        transform=transform_test,
    )

    return train_data, test_data


# download MNIST
def download_mnist_dataset():

    # create transform functions
    transform_train = transforms.Compose([
        transforms.RandomCrop(size=32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.5), (0.5)),
    ])

    transform_test = transforms.Compose([
        transforms.RandomCrop(size=32, padding=4),
        transforms.ToTensor(),
        transforms.Normalize((0.5), (0.5)),
    ])

    # create datasets
    train_data = datasets.MNIST(
        root="./data",
        download=True,
        train=True,
        transform=transform_train
    )
    validation_data = datasets.MNIST(
        root="./data",
        download=True,
        train=False,
        transform=transform_test
    )

    return train_data, validation_data