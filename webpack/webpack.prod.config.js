var webpack = require('webpack')
var BundleTracker = require('webpack-bundle-tracker')
var config = require('./webpack.base.config.js')
var CompressionPlugin = require("compression-webpack-plugin")


config.output.filename = '[name].min.js',
config.output.path = require('path').resolve('./assets/prod')

config.plugins = config.plugins.concat([
  new BundleTracker({
    filename: 'webpack/webpack-stats-prod.json',
  }),
  new webpack.DefinePlugin({
    'process.env.NODE_ENV': '"production"',
  }),
  new webpack.optimize.UglifyJsPlugin({
    mangle: true,
    compressor: {
      warnings: false,
      pure_getters: true,
      unsafe: true,
      unsafe_comps: true,
      screw_ie8: true,
    },
    output: {
      comments: false,
    },
  }),
  new webpack.NoEmitOnErrorsPlugin(),
  // new CompressionPlugin({
  //   asset: '[path].gz[query]',
  //   algorithm: 'gzip',
  //   test: /\.(js|css|html)$/,
  //   threshold: 0,
  //   minRatio: 0.8,
  // }),
])

config.module.loaders.push(
  { test: /\.jsx?$/, exclude: /node_modules/, loader: 'babel-loader' }
)

module.exports = config
