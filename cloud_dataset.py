import numpy as np
import pandas as pd
import rasterio
import torch
from typing import Optional, List
# import albumentations as A
# from albumentations.pytorch.transforms import ToTensorV2


class CloudDataset(torch.utils.data.Dataset):
    """Reads in images, transforms pixel values, and serves a
    dictionary containing chip ids, image tensors, and
    label masks (where available).
    """
    # train_transforms = A.Compose(
    #     [
    #         A.Resize(height=128, width=128),
    #         A.Rotate(limit=35, p=1.0),
    #         A.HorizontalFlip(p=0.5),
    #         A.VerticalFlip(p=0.5),
    #         A.Normalize(
    #             mean=0.0,
    #             std=1.0,
    #             max_pixel_value=255.0,
    #         ),
    #         ToTensorV2(),
    #     ],
    # )
    def __init__(
        self,
        x_paths: pd.DataFrame,
        bands: List[str],
        y_paths: Optional[pd.DataFrame] = None,
        transforms: Optional[list] = None,
    ):
        """
        Instantiate the CloudDataset class.

        Args:
            x_paths (pd.DataFrame): a dataframe with a row for each chip. There must be a column for chip_id,
                and a column with the path to the TIF for each of bands
            bands (list[str]): list of the bands included in the data
            y_paths (pd.DataFrame, optional): a dataframe with a for each chip and columns for chip_id
                and the path to the label TIF with ground truth cloud cover
            transforms (list, optional): list of transforms to apply to the feature data (eg augmentations)
        """
        self.data = x_paths
        self.label = y_paths
        self.transforms = transforms
        self.bands = bands

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx: int):
        # Loads an n-channel image from a chip-level dataframe
        img = self.data.loc[idx]
        band_arrs = []
        for band in self.bands:
            with rasterio.open(img[f"{band}_path"]) as b:
                band_arr = b.read(1).astype("float32")
            band_arrs.append(band_arr)
        x_arr = np.stack(band_arrs, axis=-1)
        
        # Load label if available
        if self.label is not None:
            label_path = self.label.loc[idx].label_path
            with rasterio.open(label_path) as lp:
                y_arr = lp.read(1).astype("float32")

        # Apply data augmentations, if provided
        if self.transforms is not None:
            augmentations = self.transforms(image=x_arr, mask=y_arr)
            
            x_arr = augmentations["image"]
            y_arr = augmentations["mask"]
            
            # x_arr = self.transforms(image=x_arr)["image"]
        # x_arr = np.transpose(x_arr, [2, 0, 1])

        # Prepare dictionary for item
        item = {"chip_id": img.chip_id, "chip": x_arr, "label": y_arr}

        return item
