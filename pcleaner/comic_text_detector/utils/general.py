# import os
# import logging
# import wandb
# import torch
#
#
# def set_logging(name=None, verbose=True):
#     for handler in logging.root.handlers[:]:
#         logging.root.removeHandler(handler)
#     # Sets level and returns logger
#     rank = int(os.getenv("RANK", -1))  # rank in world for Multi-GPU trainings
#     logging.basicConfig(
#         format="%(message)s", level=logging.INFO if (verbose and rank in (-1, 0)) else logging.WARNING
#     )
#     return logging.getLogger(name)
#
#
# LOGGER = set_logging(__name__)  # define globally (used in train.py, val.py, detect.py, etc.)
#
# LOGGERS = ("csv", "tb", "wandb")
#
# CUDA = True if torch.cuda.is_available() else False
# DEVICE = "cuda" if CUDA else "cpu"
#
# LOGGER_WANDB = "wandb"
# LOGGER_TENSORBOARD = "tb"
#
#
# class Loggers:
#     def __init__(self, hyp):
#         self.type = hyp["logger"]["type"]
#         self.epochs = hyp["train"]["epochs"]
#         self.wandb = None
#         self.writer = None
#         if self.type == LOGGER_WANDB:
#             if hyp["logger"]["project"] == "":
#                 project = "ComicTextDetector"
#             else:
#                 project = hyp["logger"]["project"]
#             if hyp["logger"]["run_id"] == "":
#                 self.wandb = wandb.init(project=project, config=hyp, resume="allow")
#             else:
#                 self.wandb = wandb.init(
#                     project=project, config=hyp, resume="must", id=hyp["logger"]["run_id"]
#                 )
#         elif self.type == LOGGER_TENSORBOARD:
#             from torch.utils.tensorboard import SummaryWriter
#
#             self.writer = SummaryWriter(hyp["data"]["save_dir"])
#
#     def on_train_batch_end(self, metrics):
#         # Callback runs on train batch end
#         if self.wandb:
#             self.wandb.log(metrics)
#         pass
#
#     def on_train_epoch_end(self, epoch, metrics):
#         LOGGER.info(f"fin epoch {epoch}/{self.epochs}, metrics: {metrics}")
#         if self.type == LOGGER_WANDB:
#             self.wandb.log(metrics)
#         elif self.type == LOGGER_TENSORBOARD:
#             for key in metrics.keys():
#                 self.writer.add_scalar(key, metrics[key], epoch)
#
#     def on_model_save(self, last, epoch, final_epoch, best_fitness, fi):
#         # Callback runs on model save event
#         if self.wandb:
#             if ((epoch + 1) % self.opt.save_period == 0 and not final_epoch) and self.opt.save_period != -1:
#                 self.wandb.log_model(last.parent, self.opt, epoch, fi, best_model=best_fitness == fi)
