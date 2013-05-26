pyannote = function() {

    var pyannote = {
        version: "0.0.1"
    };

    pyannote.extent = function(annotation) {
        var tracks = annotation.tracks;
        var t_min = d3.min(tracks, function(d) {return d.segment.start;});
        var t_max = d3.max(tracks, function(d) {return d.segment.end;});
        return [t_min, t_max];
    };

    pyannote.common_extent = function(annotations) {

        var t_min = Infinity;
        var t_max = -Infinity;

        for (var i = annotations.length - 1; i >= 0; i--) {
            var extent = pyannote.extent(annotations[i]);
            t_min = Math.min(t_min, extent[0]);
            t_max = Math.max(t_max, extent[1]);
        }
        return [t_min, t_max];
    };

    pyannote.draw_annotation = function(annotation, container, scale, color) {

        var height = container.attr("height");

        // var modality = annotation.modality;
        // var uri = annotation.uri;
        var tracks = annotation.tracks;

        var rect = container.selectAll(".track")
            .data(tracks);

        rect.select("rect")
            .attr("transform", function(d) {
                return "translate(" + scale(d.segment.start) + ", " + height*1/10 + ")";
            })
            .attr("width", function(d) {
                return scale(d.segment.end) - scale(d.segment.start);
            });

        rect.enter()
            .append("g")
                .attr("class", "track")
                .append("rect")
                .attr("transform", function(d) {
                    return "translate(" + scale(d.segment.start) + ", " + height*1/10 + ")";
                })
                .attr("width", function(d) {
                    return scale(d.segment.end) - scale(d.segment.start);
                })
                .attr("height", height*4/5)
                .style("fill", function(d) {
                    return color(d.label);
                });

    };

    pyannote.formatSeconds = function(seconds) {

        var twoFigures = d3.format("02d");
        var threeFigures = d3.format("03d");

        // h = Math.floor(seconds / 3600);
        // seconds = seconds - 3600*h;
        m = Math.floor(seconds / 60);
        seconds = seconds - 60*m;
        s = Math.floor(seconds);
        ms = Math.floor((seconds - s) * 1000);

        return twoFigures(m) + ":" + twoFigures(s) + "." + threeFigures(ms);
    };

    pyannote.draw = function(annotations, whole, detail) {

        var n = annotations.length;

        var height_axis = 20;


        var width = whole.attr("width");
        var height = whole.attr("height");

        var common_extent = pyannote.common_extent(annotations);
        var t_whole = d3.scale.linear()
            .domain(common_extent)
            .range([0, width]);

        var width_detail = detail.attr("width");
        var height_detail = detail.attr("height");

        var t_detail = d3.scale.linear()
            .domain(common_extent)
            .range([0, width_detail]);

        var color = d3.scale.category10();

        // one timeline per annotation
        var timelines = whole.selectAll(".timeline")
            .data(annotations);

        timelines
            .enter()
            .append("g")
            .attr("class", "timeline")
            .attr("height", (height-height_axis)/n)
            .attr("transform", function(d, i) {
                return "translate(0, " + i*(height-height_axis)/n + ")";
            });

        timelines
            .each(function(d) { pyannote.draw_annotation(d, d3.select(this), t_whole, color); });

        var brush = d3.svg.brush()
            .x(t_whole)
            .extent([common_extent[0] + (common_extent[1]-common_extent[0])/3,
                     common_extent[0] + 2*(common_extent[1]-common_extent[0])/3])
            .on("brush", display);

        whole.append("g")
            .attr("class", "brush")
            .call(brush)
            .selectAll("rect")
            .attr("y", 0)
            .attr("height", height);

        var axis_whole = d3.svg.axis()
            .scale(t_whole)
            .orient("bottom")
            .ticks(5)
            .tickFormat(pyannote.formatSeconds);

        var axis_whole_view = whole.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + (height - height_axis) + ")");
        axis_whole_view
            .call(axis_whole);

        var axis_detail = d3.svg.axis()
            .scale(t_detail)
            .orient("bottom")
            .ticks(5)
            .tickFormat(pyannote.formatSeconds);

        var axis_detail_view = detail.append("g")
            .attr("class", "axis")
            .attr("transform", "translate(0," + (height_detail - height_axis) + ")");
        axis_detail_view
            .call(axis_detail);

        display();

        function display() {

            // console.log(brush.extent());
            t_detail.domain(brush.extent());

            // axis.scale(t_detail);
            axis_detail_view.call(axis_detail);

            var timelines = detail.selectAll(".timeline")
                .data(annotations);

            timelines
                .attr("height", (height_detail-height_axis)/n)
                .attr("transform", function(d, i) {
                    return "translate(0, " + i*(height_detail-height_axis)/n + ")";
                })
                .each(function(d) {
                    pyannote.draw_annotation(d, d3.select(this), t_detail, color);
                });

            timelines
                .enter()
                .append("g")
                .attr("class", "timeline")
                .attr("height", (height_detail-height_axis)/n)
                .attr("transform", function(d, i) {
                    return "translate(0, " + i*(height_detail-height_axis)/n + ")";
                })
                .each(function(d) {
                    pyannote.draw_annotation(d, d3.select(this), t_detail, color);
                });
        }

    };

    return pyannote;
}();
