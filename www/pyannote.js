pyannote = function() {

    var pyannote = {
        version: "0.0.1"
    };

    //
    pyannote.start = function(track) {
        return track.segment.start;
    };

    pyannote.end = function(track) {
        return track.segment.end;
    };

    pyannote.extent = function(annotation) {
        var tracks = annotation.annotation;
        var t_min = d3.min(tracks, pyannote.start);
        var t_max = d3.max(tracks, pyannote.end);
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

    pyannote.draw_annotation = function(annotation, container, t, color) {

        var width = container.attr("width");
        var height = container.attr("height");

        var modality = annotation.modality;
        var uri = annotation.uri;
        var tracks = annotation.annotation;

        var rect = container.selectAll(".track")
            .data(tracks)
            .enter()
            .append("g")
                .attr("class", "track")
                .append("rect")
                .attr("transform", function(d) {
                    return "translate(" + t(d.segment.start) + ", " + height*1/10 + ")";
                })
                .attr("width", function(d) {return t(d.segment.end) - t(d.segment.start);})
                .attr("height", height*4/5)
                .style("fill", function(d) {return color(d.label);});

    };

    pyannote.draw = function(annotations, container) {


        var n = annotations.length;

        var width = container.attr("width");
        var height = container.attr("height");

        var common_extent = pyannote.common_extent(annotations);
        var t = d3.scale.linear()
            .domain(common_extent)
            .range([0, width]);

        var color = d3.scale.category10();

        for (var i = n - 1; i >= 0; i--) {
            var chart = container.append("g")
                .attr("height", height/n)
                .attr("transform", "translate(0, " + i*height/n + ")");
            pyannote.draw_annotation(annotations[i], chart, t, color);
        }

        var brush = d3.svg.brush()
            .x(t)
            // .on("brush", pyannote.draw);

        container.append("g")
            .attr("class", "brush")
            .call(brush)
            .selectAll("rect")
            .attr("y", 0)
            .attr("height", 200);

    };


    return pyannote;
}();
