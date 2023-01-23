# import onnx
# import onnxsim
# import torch
# import torch.nn as nn
# from models.yolov5.common import Conv
# from models.yolov5.yolo import Detect
#
#
# class SiLU(nn.Module):  # export-friendly version of nn.SiLU()
#     @staticmethod
#     def forward(x):
#         return x * torch.sigmoid(x)
#
#
# def concate_models(blk_weights, seg_weights, det_weights, save_path):
#     textdetector_dict = dict()
#     textdetector_dict["blk_det"] = torch.load(blk_weights, map_location="cpu")
#     textdetector_dict["text_seg"] = torch.load(seg_weights, map_location="cpu")["weights"]
#     textdetector_dict["text_det"] = torch.load(det_weights, map_location="cpu")["weights"]
#     torch.save(textdetector_dict, save_path)
#
#
# def export_onnx(model, im, file, opset, train=False, simplify=True, dynamic=False, inplace=False):
#     # YOLOv5 ONNX export
#     f = file + ".onnx"
#     for k, m in model.named_modules():
#         if isinstance(m, Conv):  # assign export-friendly activations
#             if isinstance(m.act, nn.SiLU):
#                 m.act = SiLU()
#         elif isinstance(m, Detect):
#             m.inplace = inplace
#             m.onnx_dynamic = False
#     torch.onnx.export(
#         model,
#         im,
#         f,
#         verbose=False,
#         opset_version=opset,
#         training=torch.onnx.TrainingMode.TRAINING if train else torch.onnx.TrainingMode.EVAL,
#         do_constant_folding=not train,
#         input_names=["images"],
#         output_names=["blk", "seg", "det"],
#         dynamic_axes={
#             "images": {0: "batch", 2: "height", 3: "width"},  # shape(1,3,640,640)
#             "output": {0: "batch", 1: "anchors"},  # shape(1,25200,85)
#         }
#         if dynamic
#         else None,
#     )
#
#     # Checks
#     model_onnx = onnx.load(f)  # load onnx model
#     onnx.checker.check_model(model_onnx)  # check onnx model
#
#     model_onnx, check = onnxsim.simplify(
#         model_onnx, dynamic_input_shape=dynamic, input_shapes={"images": list(im.shape)} if dynamic else None
#     )
#     assert check, "assert check failed"
#     onnx.save(model_onnx, f)
