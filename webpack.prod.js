const path = require('path')
const { CleanWebpackPlugin } = require('clean-webpack-plugin')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const WebpackBundleTracker = require('webpack-bundle-tracker')

module.exports = {
  mode: 'production',
  entry: {
    breakpointCalc: './static/javascript/breakpointCalc',
    goodToGo: './static/javascript/goodToGo',
    lists: './static/javascript/lists',
  },
  output: {
    filename: '[name]_[contenthash].js',
    path: path.resolve(__dirname, 'staticfiles/bundles'),
    publicPath: '',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env'],
          }
        },
      },
      {
        test: /\.(sa|sc|c)ss$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          'sass-loader',
        ]
      },
    ]
  },
  plugins: [
    new WebpackBundleTracker({
      filename: './webpack-stats-prod.json',
    }),
    new MiniCssExtractPlugin({
      filename: '[name]_[contenthash].css',
    }),
    new CleanWebpackPlugin(),
  ],
}
