import numpy as np
import torch
from torch import nn


class Encoder(nn.Module):
    def __init__(self, in_channels: int = 3, latent_dim : int = 256, hidden_dims: list = [32, 64, 128, 256], im_dim: int = 32, feedforward_block_dim: int = 1024):
        super().__init__()

        # check if the given image has height and width that are powers of 2
        assert im_dim==2**int(np.log2(im_dim)), "Error: The image sizes must be a power of 2"

        # dimensions of the outputs of the convolution part of the encoder
        encoder_conv_output_H_dim = im_dim // 2 ** len(hidden_dims)
        encoder_conv_output_CxHxW_dim = hidden_dims[-1]*(encoder_conv_output_H_dim ** 2)

        modules = []

        for hidden_dim in hidden_dims:
            # downscaling factor equal to 2
            modules.append(
                nn.Sequential(
                    nn.Conv2d(
                        in_channels=in_channels,
                        out_channels=hidden_dim,
                        kernel_size= 3,
                        stride= 2,
                        padding  = 1
                    ),
                    nn.BatchNorm2d(hidden_dim),
                    nn.LeakyReLU()
                )
            )
            in_channels = hidden_dim

        self.encoder = nn.Sequential(*modules)

        self.feedforward_block = nn.Sequential(
                                    nn.Linear(encoder_conv_output_CxHxW_dim, feedforward_block_dim),
                                    nn.BatchNorm1d(feedforward_block_dim),
                                    nn.LeakyReLU()
                                 )
        # encoded space variables
        self.feedforward_mu = nn.Linear(feedforward_block_dim, latent_dim)
        self.feedforward_sigma = nn.Linear(feedforward_block_dim, latent_dim)


    def forward(self, x):
        x = self.encoder(x)
        x = torch.flatten(x, start_dim=1)
        x = self.feedforward_block(x)

        mu = self.feedforward_mu(x)
        log_var = self.feedforward_sigma(x)

        return mu, log_var
    

def sampling(mu, sigma):

    epsilon = torch.randn_like(sigma) # with dimension: batch * latent_dim
    epsilon = epsilon.type_as(mu) # Setting epsilon to be .cuda when using GPU training 
    
    z = mu + epsilon * sigma

    return z


class Decoder(nn.Module):
    def __init__(self, out_channels: int = 3, latent_dim : int = 256, hidden_dims: list = [256, 128, 64, 32], im_dim: int = 32, feedforward_block_dim: int = 1024):
        super().__init__()

        # dimensions of the inputs of the convolution part of the decoder
        decoder_conv_input_H_dim = im_dim // 2 ** len(hidden_dims)
        decoder_conv_input_CxHxW_dim = hidden_dims[0]*(decoder_conv_input_H_dim ** 2)
        # check if the feedforward block dimensions are coherent with respect the convolution operations performed
        error_message = f"Error: The feedforward block dimensions are not compatible with the convolution blocks dimensions \
            to obtain the initial image.\nSuggested dimension: {decoder_conv_input_CxHxW_dim}"
        assert decoder_conv_input_CxHxW_dim==feedforward_block_dim, error_message

        self.feedforward_block_dim  = feedforward_block_dim
        self.dim_channel_0 = hidden_dims[0]

        # feedforward block
        self.feedforward_block = nn.Sequential(
            nn.Linear(latent_dim, feedforward_block_dim),
            nn.BatchNorm1d(feedforward_block_dim)
        )

        # deconvolution blocks
        modules = []

        for i in range(len(hidden_dims) - 1):
            # upscaling factor equal to 2
            modules.append(
                nn.Sequential(
                    nn.ConvTranspose2d(
                        in_channels=hidden_dims[i],
                        out_channels=hidden_dims[i + 1],
                        kernel_size= 3,
                        stride= 2,
                        padding  = 1,
                        output_padding=1    # necessary to adjust the dimensions: it adds zeros on the bottom right of the output
                    ),
                    nn.BatchNorm2d(hidden_dims[i + 1]),
                    nn.LeakyReLU())
            )
        
        self.decoder = nn.Sequential(*modules)

        # last upscale to obtain the image dimension
        self.final_block = nn.Sequential(
            nn.ConvTranspose2d(
                in_channels=hidden_dims[-1],
                out_channels=hidden_dims[-1],
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=1
            ),
            nn.BatchNorm2d(hidden_dims[-1]),
            nn.LeakyReLU(),
            nn.Conv2d(
                in_channels=hidden_dims[-1], 
                out_channels= out_channels,
                kernel_size= 3, 
                padding= 1
            ),
            nn.Tanh()
        )


    def forward(self, z):
        z = self.feedforward_block(z)
        H_dim = int(np.sqrt(self.feedforward_block_dim/self.dim_channel_0))
        z = z.view(-1, self.dim_channel_0, H_dim, H_dim)    # z.view(z.size(0),-1)
        x = self.decoder(z)
        x = self.final_block(x)

        return x


class VAE(nn.Module):
    def __init__(self, encoder, decoder):
        super().__init__()

        self.encoder = encoder
        self.decoder = decoder

        # learnable parameter for the gaussian likelihood in the reconstruction_loss
        self.log_scale = nn.Parameter(torch.Tensor([0.0]))

    def forward(self, x):
        mu, log_var = self.encoder(x)
        sigma = torch.exp(0.5 * log_var)
        z = sampling(mu, sigma)
        x_hat = self.decoder(z)

        return x_hat, mu, sigma, z
