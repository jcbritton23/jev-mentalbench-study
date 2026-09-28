# Data policy

The MentalBench CSV is hosted by [the dataset authors on Hugging Face](https://huggingface.co/datasets/hysong/MentalBench); this repository links to it and does not redistribute it. The source repository declares CC BY 4.0. It publishes a single `train` split without a development/test partition. The split files here assign source-related groups to exploration or holdout and contain no case descriptions, options, or answer text.

Download the data from its source into `data/raw/mentalbench.csv` only after reviewing its current license and access terms. The `data/raw/` directory and text-bearing intermediate files are ignored by Git. The optional EmpatheticDialogues track is outside the scope of this MentalBench repository and is not included.

See [the dataset audit](../docs/AUDIT.md) for the inspected schema, license/access notes, grouping rationale, and split counts.
