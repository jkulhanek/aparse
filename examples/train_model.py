#!/bin/env python
import argparse
from aparse import ConditionalType, add_argparse_arguments
from dataclasses import dataclass
import pytorch_lightning as pl


@dataclass
class GPT2Config:
    n_head: int = 12
    d_model: int = 768
    dropout: float = 0.1
    n_layer: int = 12
    weight_decay: float = 0.01
    learning_rate: float = 2.5e-4
    batch_size: int = 64
    gradient_clip_val: float = 0.0
    sequence_size: int = 20
    total_steps: int = 300000


@dataclass
class RobertaConfig:
    n_head: int = 12
    d_model: int = 512
    n_layer: int = 12
    learning_rate: float = 2.5e-4
    gradient_clip_val: float = 1.0
    sequence_size: int = 20
    total_steps: int = 600000


class ModelSwitch(ConditionalType, prefix=False):
    gpt2: GPT2Config
    bert: RobertaConfig


@add_argparse_arguments()
def build_trainer(
        job_dir: str,
        total_steps: int,
        gradient_clip_val: float,
        epochs: int = 100,
        num_gpus: int = 8,
        num_nodes: int = 1):
    logger = pl.loggers.TensorBoardLogger(save_dir=job_dir)
    kwargs = dict(num_nodes=num_nodes)
    if num_gpus > 0:
        kwargs.update(dict(gpus=num_gpus, accelerator='ddp'))

    # Split training to #epochs epochs
    limit_train_batches = 1 + total_steps // epochs

    # Save every 2 epochs
    validation_steps = max(1, min((total_steps // epochs) // 10, 100))
    model_checkpoint = pl.callbacks.ModelCheckpoint(monitor='val_loss')
    trainer = pl.Trainer(
        weights_save_path=job_dir,
        max_epochs=epochs,
        val_check_interval=limit_train_batches,
        gradient_clip_val=gradient_clip_val,
        limit_val_batches=validation_steps,
        limit_train_batches=limit_train_batches,
        logger=logger,
        callbacks=[pl.callbacks.LearningRateMonitor('step'), model_checkpoint], **kwargs)
    return trainer


@add_argparse_arguments
class CustomDataModule(pl.LightningDataModule):
    def __init__(self, dataset: str, batch_size: int, num_workers: int = 8):
        super().__init__()
        # Omitted for brevity


@add_argparse_arguments()
def build_model(model: ModelSwitch):
    # Omitted for brevity
    return pl.LightningModule()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', choices=['train', 'evaluate'], default='train')
    parser = build_trainer.add_argparse_arguments(parser)
    parser = CustomDataModule.add_argparse_arguments(parser)
    parser = build_model.add_argparse_arguments(parser)
    args = parser.parse_args()

    # Build the actual model
    model = build_model.from_argparse_arguments(args)

    # Build trainer
    trainer = build_trainer.from_argparse_arguments(args)

    # Start the training
    datamodule = CustomDataModule.from_argparse_args(args)
    if args.task == 'train':
        trainer.fit(model, datamodule=datamodule)
    elif args.task == 'evaluate':
        trainer.test(model, datamodule=datamodule)


if __name__ == '__main__':
    main()

# Try the following:
# python train_model.py
# python train_model.py --model gpt2
