# Generates a static page per tag at /tags/<slug>/ listing matching posts.
module TagPages
  class TagPage < Jekyll::Page
    def initialize(site, base, tag, slug, posts)
      @site = site
      @base = base
      @dir  = File.join("tags", slug)
      @name = "index.html"

      process(@name)
      read_yaml(File.join(base, "_layouts"), "tag.html")

      data["layout"]    = "tag"
      data["tag"]       = tag
      data["tag_slug"]  = slug
      data["tag_posts"] = posts
      data["title"]     = "##{tag}"
    end
  end

  class Generator < Jekyll::Generator
    safe true
    priority :low

    def generate(site)
      groups = Hash.new { |h, k| h[k] = [] }
      slugs  = {}

      site.posts.docs.each do |post|
        Array(post.data["tags"]).each do |tag|
          tag = tag.to_s.strip
          next if tag.empty?
          slug = Jekyll::Utils.slugify(tag)
          slugs[slug] ||= tag
          groups[slug] << post
        end
      end

      groups.each do |slug, posts|
        posts = posts.sort_by { |p| p.date }.reverse
        site.pages << TagPage.new(site, site.source, slugs[slug], slug, posts)
      end
    end
  end
end
