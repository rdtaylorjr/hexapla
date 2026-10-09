# Hexapla

## About

This is the
[text-fabric](https://github.com/annotation/text-fabric)
representation of the Göttingen Hexapla Database, with the Hexaplaric material of
2 Samuel and the Psalms.

See [about](docs/about.md) for more information about this textual source,
and for the copyright and license of the data.

The conversion to Text-Fabric is the work of Rusty Taylor.

There is more information on the
[transcription](docs/transcription.md).

## How to use

### Having Text-Fabric installed

This data can be processed by
[Text-Fabric](https://annotation.github.io/text-fabric/tf).

After [installing Text-Fabric](https://annotation.github.io/text-fabric/tf/about/install.html),
you can start the Text-Fabric browser by this command

```sh
text-fabric rdtaylorjr/hexapla
```

Alternatively, you can work in a Jupyter notebook and say

```python
from tf.app import use

A = use('rdtaylorjr/hexapla')
```

See also
[start](tutorial/start.ipynb).

# Author

Rusty Taylor
