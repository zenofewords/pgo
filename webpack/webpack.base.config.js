var path = require('path')
var webpack = require('webpack')
var ExtractTextPlugin = require('extract-text-webpack-plugin')
var OptimizeCssAssetsPlugin = require('optimize-css-assets-webpack-plugin')


module.exports = {
  context: __dirname,
  entry: [
      '../assets/static/index'
  ],

  output: {
      path: path.resolve('./assets/bundles/'),
      filename: '[name].min.js',
  },

  plugins: [
    new ExtractTextPlugin("styles.css"),
    new OptimizeCssAssetsPlugin(),
  ],
  module: {
    loaders: [{
        test: /\.jsx?$/,
        exclude: /node_modules/,
        loaders: ['react-hot', 'babel'],
      }, {
          test: /\.css$/,
          loader: ExtractTextPlugin.extract(["css-loader"]),
      },
    ],
  },
  resolve: {
    modulesDirectories: ['node_modules'],
    extensions: ['', '.js', '.jsx']
  },
}
