"""
Clinical Toxicity (clintox) dataset loader.
@author Caleb Geniesse
"""

from __future__ import division
from __future__ import unicode_literals

import os
import logging
import deepchem

logger = logging.getLogger(__name__)


def load_clintox(featurizer='ECFP', split='index', reload=True):
  """Load clintox datasets."""

  data_dir = deepchem.utils.get_data_dir()
  if reload:
    save_dir = os.path.join(data_dir,
                            "clintox/" + featurizer + "/" + str(split))

  dataset_file = os.path.join(data_dir, "clintox.csv.gz")
  if not os.path.exists(dataset_file):
    deepchem.utils.download_url(
        'http://deepchem.io.s3-website-us-west-1.amazonaws.com/datasets/clintox.csv.gz'
    )

  logger.info("About to load clintox dataset.")
  dataset = deepchem.utils.save.load_from_disk(dataset_file)
  clintox_tasks = dataset.columns.values[1:].tolist()
  logger.info("Tasks in dataset: %s" % (clintox_tasks))
  logger.info("Number of tasks in dataset: %s" % str(len(clintox_tasks)))
  logger.info("Number of examples in dataset: %s" % str(dataset.shape[0]))
  if reload:
    loaded, all_dataset, transformers = deepchem.utils.save.load_dataset_from_disk(
        save_dir)
    if loaded:
      return clintox_tasks, all_dataset, transformers
  # Featurize clintox dataset
  logger.info("About to featurize clintox dataset.")
  if featurizer == 'ECFP':
    featurizer = deepchem.feat.CircularFingerprint(size=1024)
  elif featurizer == 'GraphConv':
    featurizer = deepchem.feat.ConvMolFeaturizer()
  elif featurizer == 'Weave':
    featurizer = deepchem.feat.WeaveFeaturizer()
  elif featurizer == 'Raw':
    featurizer = deepchem.feat.RawFeaturizer()

  loader = deepchem.data.CSVLoader(
      tasks=clintox_tasks, smiles_field="smiles", featurizer=featurizer)
  dataset = loader.featurize(dataset_file, shard_size=8192)

  # Transform clintox dataset
  if split is None:
    transformers = [
        deepchem.trans.BalancingTransformer(transform_w=True, dataset=dataset)
    ]

    logger.info("Split is None, about to transform data.")
    for transformer in transformers:
      dataset = transformer.transform(dataset)

    return clintox_tasks, (dataset, None, None), transformers

  splitters = {
      'index': deepchem.splits.IndexSplitter(),
      'random': deepchem.splits.RandomSplitter(),
      'scaffold': deepchem.splits.ScaffoldSplitter()
  }
  splitter = splitters[split]
  logger.info("About to split data with {} splitter.".format(split))
  train, valid, test = splitter.train_valid_test_split(dataset)

  transformers = [
      deepchem.trans.BalancingTransformer(transform_w=True, dataset=train)
  ]

  logger.info("About to transform data.")
  for transformer in transformers:
    train = transformer.transform(train)
    valid = transformer.transform(valid)
    test = transformer.transform(test)

  if reload:
    deepchem.utils.save.save_dataset_to_disk(save_dir, train, valid, test,
                                             transformers)

  return clintox_tasks, (train, valid, test), transformers
